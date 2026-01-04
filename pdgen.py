#!/usr/bin/env python3
"""Generate Pure Data patch files programmatically."""

class PdPatch:
    def __init__(self, width=900, height=800):
        self.width = width
        self.height = height
        self.objects = []
        self.connections = []
        self.subpatches = {}  # name -> PdPatch

    def obj(self, x, y, *args):
        """Add an object, return its index."""
        idx = len(self.objects)
        self.objects.append(('obj', x, y, ' '.join(str(a) for a in args)))
        return idx

    def msg(self, x, y, content):
        """Add a message box, return its index."""
        idx = len(self.objects)
        # Escape special chars for Pd file format
        content = content.replace(';', '\\;').replace(',', '\\,')
        self.objects.append(('msg', x, y, content))
        return idx

    def text(self, x, y, content):
        """Add a comment, return its index."""
        idx = len(self.objects)
        self.objects.append(('text', x, y, content))
        return idx

    def subpatch(self, x, y, name, patch):
        """Add a subpatch, return its index."""
        idx = len(self.objects)
        self.objects.append(('subpatch', x, y, name, patch))
        self.subpatches[name] = patch
        return idx

    def connect(self, src_idx, src_outlet, dst_idx, dst_inlet=0):
        """Connect two objects."""
        self.connections.append((src_idx, src_outlet, dst_idx, dst_inlet))

    def render(self):
        """Render to Pd file format."""
        lines = [f"#N canvas 100 100 {self.width} {self.height} 12;"]

        for item in self.objects:
            if item[0] == 'obj':
                _, x, y, content = item
                lines.append(f"#X obj {x} {y} {content};")
            elif item[0] == 'msg':
                _, x, y, content = item
                lines.append(f"#X msg {x} {y} {content};")
            elif item[0] == 'text':
                _, x, y, content = item
                lines.append(f"#X text {x} {y} {content};")
            elif item[0] == 'subpatch':
                _, x, y, name, patch = item
                # Render subpatch inline
                sub_lines = patch.render().split('\n')
                # Replace first line with subpatch header
                sub_lines[0] = f"#N canvas 0 0 600 400 {name} 0;"
                # Add restore line
                sub_content = '\n'.join(sub_lines)
                lines.append(sub_content)
                lines.append(f"#X restore {x} {y} pd {name};")

        for src, src_out, dst, dst_in in self.connections:
            lines.append(f"#X connect {src} {src_out} {dst} {dst_in};")

        return '\n'.join(lines)

    def save(self, filename):
        """Save to file."""
        with open(filename, 'w') as f:
            f.write(self.render())
            f.write('\n')


def make_brain():
    """Create the brain patch."""
    p = PdPatch()

    # Header comments
    p.text(20, 20, "=== PURE DATA PHYSICAL - BRAIN ===")
    p.text(20, 45, "Dynamic module instantiation")

    # Voices subpatch - with static receive for freq control
    voices = PdPatch()
    voices.obj(50, 50, "namecanvas", "voices")  # id 0
    v_vol = voices.obj(50, 200, "*~", "0.3")    # id 1
    v_env = voices.obj(50, 250, "env~")         # id 2
    v_print = voices.obj(50, 300, "print", "signal-level")  # id 3
    # Static receive for freq - will connect to dynamically created osc~
    v_recv = voices.obj(200, 50, "receive", "module-1-freq")  # id 4
    v_recv_print = voices.obj(300, 50, "print", "osc-freq-in")  # id 5
    voices.connect(v_vol, 0, v_env, 0)
    voices.connect(v_env, 0, v_print, 0)
    voices.connect(v_recv, 0, v_recv_print)  # debug: print what goes to osc~

    p.subpatch(600, 100, "voices", voices)

    # OSC receive chain
    net = p.obj(50, 100, "netreceive", "-u", "-b", "8000")
    osc = p.obj(50, 130, "oscparse")
    trim = p.obj(50, 160, "list", "trim")
    route = p.obj(50, 190, "route", "hello", "param", "goodbye")

    p.connect(net, 0, osc)
    p.connect(osc, 0, trim)
    p.connect(trim, 0, route)

    # Hello handling
    hello_print = p.obj(50, 240, "print", "hello-raw")
    unpack = p.obj(50, 280, "unpack", "s", "s")

    p.connect(route, 0, hello_print)
    p.connect(route, 0, unpack)

    # Debug prints for unpack
    p.obj(180, 280, "print", "module-id")
    type_print = p.obj(180, 320, "print", "type")

    # Param handling: /param module-id param-name value
    # For now, hardcode module-1 freq -> send to module-1-freq
    param_print = p.obj(450, 280, "print", "param-raw")
    param_unpack = p.obj(200, 280, "unpack", "s", "s", "f")  # module-id, param-name, value
    # Use select to match param-name, then use value
    param_sel = p.obj(200, 320, "select", "freq")  # match param name
    param_f = p.obj(280, 320, "f")  # store value, bang to output
    param_send = p.obj(200, 400, "send", "module-1-freq")  # send to osc~
    param_done = p.obj(350, 400, "print", "sent-freq")

    p.connect(route, 1, param_print)
    p.connect(route, 1, param_unpack)
    p.connect(param_unpack, 1, param_sel)    # param-name -> select
    p.connect(param_unpack, 2, param_f, 1)   # value -> f right inlet (store)
    p.connect(param_sel, 0, param_f)         # freq match -> bang f -> output value
    p.connect(param_f, 0, param_send)        # value -> send
    p.connect(param_f, 0, param_done)        # also print

    goodbye_print = p.obj(450, 240, "print", "goodbye")
    p.connect(route, 2, goodbye_print)

    # Route by module type - use select instead of route for symbols
    p.text(20, 360, "=== TYPE ROUTING ===")
    sel = p.obj(50, 400, "select", "oscillator", "filter")
    osc_print = p.obj(200, 440, "print", "got-oscillator")

    p.connect(unpack, 1, sel)
    p.connect(sel, 0, osc_print)

    # Dynamic creation - create osc~ and connect to static receive
    # voices has: 0=namecanvas, 1=*~, 2=env~, 3=print, 4=receive, 5=print recv
    # We'll create:
    #   6: osc~ 440 (the oscillator)
    # Then connect: 4->6 (static recv -> osc~), 6->1 (osc~ -> volume)
    trig = p.obj(50, 480, "t", "b")
    create_msg = p.msg(50, 520,
        "; voices obj 200 150 osc~ 100"  # id 6 - start at 100Hz
        " ; voices connect 4 0 6 0"      # receive -> osc~
        " ; voices connect 6 0 1 0"      # osc~ -> *~
        " ; pd dsp 1"
        " ;;"
    )
    done_print = p.obj(50, 560, "print", "triggered-create")

    p.connect(sel, 0, trig)
    p.connect(trig, 0, create_msg)
    # msg sends to receivers, not outlet - add bang to confirm it triggered
    bang_print = p.obj(200, 480, "print", "create-triggered")
    p.connect(trig, 0, bang_print)

    return p


if __name__ == "__main__":
    patch = make_brain()
    patch.save("brain.pd")
    print("Generated brain.pd")
