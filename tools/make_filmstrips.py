"""Still images of the animations for the PDF edition.

A PDF cannot play the matplotlib animations of the main chapters, so the PDF
shows four frames of each one instead. This script runs the python cells of
each chapter in order (skipping the lines that encode videos), catches every
FuncAnimation that is created, and saves four of its frames, evenly spaced
from the first to the last, as figures/pdf/<chapter>_anim<k>.png.

Usage:  python3 tools/make_filmstrips.py      (rerun after changing an animation)
"""
import os
import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'figures' / 'pdf'
CHAPTERS = ['ch_x1_Parabolic_PDEs', 'ch_x2_Hyperbolic_PDEs']
SKIP = re.compile(r'to_html5_video|to_jshtml|\.save\(')

created = []
_init = animation.FuncAnimation.__init__


def _record(self, *args, **kwargs):
    _init(self, *args, **kwargs)
    created.append(self)


animation.FuncAnimation.__init__ = _record


def frame_image(anim, frame):
    artists = anim._func(frame, *anim._args) or []
    for a in artists:            # blitted artists are skipped by a plain draw()
        a.set_animated(False)
    anim._fig.canvas.draw()
    return np.asarray(anim._fig.canvas.buffer_rgba()).copy()


def filmstrip(anim, path):
    frames = list(anim.new_frame_seq())
    if anim._init_func is not None:
        anim._init_func()
    picks = [frames[round(i * (len(frames) - 1) / 3)] for i in range(4)]
    images = [frame_image(anim, f) for f in picks]
    h, w = images[0].shape[:2]
    fig, axes = plt.subplots(2, 2, figsize=(2 * w / 100, 2 * h / 100), dpi=100)
    for ax, img in zip(axes.flat, images):
        ax.imshow(img)
        ax.axis('off')
    fig.subplots_adjust(0, 0, 1, 1, 0.02, 0.02)
    fig.savefig(path, dpi=100)
    plt.close(fig)


def cells(qmd):
    """(code, is_animation) for each python cell that is evaluated."""
    text = qmd.read_text(encoding='utf-8')
    for body in re.findall(r'^```\{python\}\n(.*?)^```', text, re.S | re.M):
        if re.search(r'^#\s?\|\s*eval:\s*false', body, re.M):
            continue
        code = '\n'.join('pass' if SKIP.search(l) else l for l in body.split('\n'))
        yield code, 'FuncAnimation' in body


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    os.chdir(ROOT)
    for name in CHAPTERS:
        matplotlib.rcdefaults()          # each chapter runs in a fresh kernel when rendered
        matplotlib.use('Agg')
        namespace = {'__name__': '__main__', 'display': lambda *a, **k: None}
        k = 0
        for code, is_anim in cells(ROOT / f'{name}.qmd'):
            created.clear()
            exec(compile(code, name, 'exec'), namespace)
            for anim in created:
                k += 1
                path = OUT / f'{name}_anim{k}.png'
                filmstrip(anim, path)
                print('wrote', path.relative_to(ROOT))
            if is_anim:
                plt.close('all')


if __name__ == '__main__':
    main()
