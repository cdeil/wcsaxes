import numpy as np

from matplotlib.text import Text

from .frame import RectangularFrame


def sort_using(X, Y):
    return [x for (y,x) in sorted(zip(Y,X))]


class TickLabels(Text):

    def __init__(self, frame, *args, **kwargs):
        self.clear()
        self._frame = frame
        super(TickLabels, self).__init__(*args, **kwargs)
        self.set_clip_on(True)
        self.set_visible_axes('all')
        self._bbox_list = []
        self.pad = 0.3

    def clear(self):
        self.world = {}
        self.pixel = {}
        self.angle = {}
        self.text = {}
        self.disp = {}

    def add(self, axis, world, pixel, angle, text, axis_displacement):
        if axis not in self.world:
            self.world[axis] = [world]
            self.pixel[axis] = [pixel]
            self.angle[axis] = [angle]
            self.text[axis] = [text]
            self.disp[axis] = [axis_displacement]
        else:
            self.world[axis].append(world)
            self.pixel[axis].append(pixel)
            self.angle[axis].append(angle)
            self.text[axis].append(text)
            self.disp[axis].append(axis_displacement)

    def sort(self):
        """
        Sort by axis displacement, which allows us to figure out which parts
        of labels to not repeat.
        """
        for axis in self.world:
            self.world[axis] = sort_using(self.world[axis], self.disp[axis])
            self.pixel[axis] = sort_using(self.pixel[axis], self.disp[axis])
            self.angle[axis] = sort_using(self.angle[axis], self.disp[axis])
            self.text[axis] = sort_using(self.text[axis], self.disp[axis])
            self.disp[axis] = sort_using(self.disp[axis], self.disp[axis])

    def simplify_labels(self):
        """
        Figure out which parts of labels can be dropped to avoid repetition.
        """
        self.sort()
        for axis in self.world:
            t1 = self.text[axis][0]
            for i in range(1, len(self.world[axis])):
                t2 = self.text[axis][i]
                if len(t1) != len(t2):
                    t1 = self.text[axis][i]
                    continue
                start = 0
                for j in range(len(t1)):
                    if t1[j] != t2[j]:
                        break
                    if t1[j] not in '-0123456789.':
                        start = j + 1
                if start == 0:
                    t1 = self.text[axis][i]
                else:
                    self.text[axis][i] = self.text[axis][i][start:]

    def set_visible_axes(self, visible_axes):
        self._visible_axes = visible_axes

    def get_visible_axes(self):
        if self._visible_axes == 'all':
            return self.world.keys()
        else:
            return [x for x in self._visible_axes if x in self.world]


    def get_ticklabels_bbox_list(self):
        """
        Returns the bounding box list of all the ticklabels
        """
        return self._bbox_list

    def draw(self, renderer, bboxes):

        self.simplify_labels()

        text_size = renderer.points_to_pixels(self.get_size())

        for axis in self.get_visible_axes():

            for i in range(len(self.world[axis])):

                self.set_text(self.text[axis][i])

                x, y = self.pixel[axis][i]

                if isinstance(self._frame, RectangularFrame):

                    # This is just to preserve the current results, but can be
                    # removed next time the reference images are re-generated.

                    if np.abs(self.angle[axis][i]) < 45.:
                        ha = 'right'
                        va = 'bottom'
                        dx = - text_size * 0.5
                        dy = - text_size * 0.5
                    elif np.abs(self.angle[axis][i] - 90.) < 45:
                        ha = 'center'
                        va = 'bottom'
                        dx = 0
                        dy = - text_size * 1.5
                    elif np.abs(self.angle[axis][i] - 180.) < 45:
                        ha = 'left'
                        va = 'bottom'
                        dx = text_size * 0.5
                        dy = - text_size * 0.5
                    else:
                        ha = 'center'
                        va = 'bottom'
                        dx = 0
                        dy = text_size * 0.2

                    self.set_position((x + dx, y + dy))
                    self.set_ha(ha)
                    self.set_va(va)

                else:

                    # This is the more general code for arbitrarily oriented
                    # axes

                    # Set initial position and find bounding box
                    self.set_position((x, y))
                    bb = super(TickLabels, self).get_window_extent(renderer)

                    # Find width and height, as well as angle at which we
                    # transition which side of the label we use to anchor the
                    # label.
                    width = bb.width
                    height = bb.height
                    theta = np.tan(height / width)

                    # Project axis angle onto bounding box
                    ax = np.cos(np.radians(self.angle[axis][i]))
                    ay = np.sin(np.radians(self.angle[axis][i]))

                    # Set anchor point for label
                    if np.abs(self.angle[axis][i]) < 45.:
                        dx = width
                        dy = ay * height
                    elif np.abs(self.angle[axis][i] - 90.) < 45:
                        dx = ax * width
                        dy = height
                    elif np.abs(self.angle[axis][i] - 180.) < 45:
                        dx = -width
                        dy = ay * height
                    else:
                        dx = ax * width
                        dy = -height

                    dx *= 0.5
                    dy *= 0.5

                    # Find normalized vector along axis normal, so as to be
                    # able to nudge the label away by a constant padding factor

                    dist = np.hypot(dx, dy)

                    ddx = dx / dist
                    ddy = dy / dist

                    dx += ddx * text_size * self.pad
                    dy += ddy * text_size * self.pad

                    self.set_position((x - dx, y - dy))
                    self.set_ha('center')
                    self.set_va('center')

                bb = super(TickLabels, self).get_window_extent(renderer)

                # TODO: the problem here is that we might get rid of a label
                # that has a key starting bit such as -0:30 where the -0
                # might be dropped from all other labels.

                if bb.count_overlaps(bboxes) == 0:
                    super(TickLabels, self).draw(renderer)
                    bboxes.append(bb)
                    self._bbox_list.append(bb)
