
class Entry:

    def __init__(self, size=1, order=0):
        self.bounds = None
        self.depth = 0
        self.size = size
        self.order = order

    def __cmp__(self, other):
        if not isinstance(other, Entry):
            raise TypeError()
        return -cmp(self.size, other.size)

class Rect:

    def __init__(self, x=None, y=None, w=None, h=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def __str__(self):
        return '(%.2f, %.2f, %.2f, %.2f)' % (self.x, self.y, self.w, self.h)

ASCENDING=0
DESCENDING=1
VERTICAL=2
HORIZONTAL=3

class AbstractLayout(object):

    name = 'Abstract'

    def __init__(self):
        self.orientation = ASCENDING

    def layout(self, entries, bounds):
        """
        Compute the layout of the entries in the map.  This is the primary
        function which subclasses should implement.

        :Parameters:
            - `entries` : A list of Entry objects which will be in the map.
            - `bounds` : A 2-tuple of (width, height)

        :Returns:
            - Nothing; the position of the Entry objects are changed.
        """

    def totalSize(self, entries, start=0, end=-1):
        if end == -1:
            end = len(entries)
        sum = 0
        for entry in entries:
            sum += entry.size
        return sum

    def sliceLayout(self, entries, start=0, end=-1, bounds=None, 
            orientation=VERTICAL, order=ASCENDING):
        if end == -1:
            end = len(entries)
        assert bounds != None
        total = self.totalSize(entries, start, end)
        a = 0
        for i in entries[start:end]:
            r = Rect()
            b = i.size / total
            if orientation == VERTICAL:
                r.x = bounds.x
                r.w = bounds.w
                if order == ASCENDING:
                    r.y = bounds.y + bounds.h*a;
                else:
                    r.y = bounds.y + bounds.h*(1-a-b)
                r.h = bounds.h * b
            else:
                if order == ASCENDING:
                    r.x = bounds.x + bounds.w*a
                else:
                    r.x = bounds.x + bounds.w*(1-a-b)
                r.w = bounds.w * b
                r.y = bounds.y
                r.h = bounds.h
            i.bounds = r
            a += b

BEST=4
ALTERNATE=5
class SliceLayout(AbstractLayout):

    name = "Slice and Dice"

    def __init__(self):
        self.orientation = ALTERNATE

    def layout(self, entries, bounds):
        if len(entries) == 0:
            return
        if self.orientation == BEST:
            self.layoutBest(entries, bounds=bounds)
        elif self.orientation == ALTERNATE:
            self.layoutAlt(entries, bounds=bounds)
        else:
            raise ValueError("Unknown Orientation: %s" % str(self.orientation))

    def layoutBest(self, entries, start=0, end=-1, bounds=None, \
            order=ASCENDING):
        assert bounds != None
        if end == -1:
            end = len(entries)
        if bounds.w > bounds.h:
            o = HORIZONTAL
        else:
            o = VERTICAL
        self.sliceLayout(entries, start, end, bounds, o, order)

    def layoutAlt(self, entries, bounds):
        if entries[0].depth % 2 == 0:
            o = VERTICAL
        else:
            o = HORIZONTAL
        self.sliceLayout(entries, bounds=bounds, orientation=o)
        
class SquarifiedLayout(SliceLayout):

    def layout(self, entries, start=0, end=-1, bounds=None, isSorted=False):
        assert bounds != None
        if end == -1:
            end = len(entries)
        if not isSorted:
            entries.sort()
        if start > end:
            return
        if end-start < 2:
            self.layoutBest(entries, start, end, bounds)
            return
        x = bounds.x
        y = bounds.y
        w = bounds.w
        h = bounds.h

        total = self.totalSize(entries, start, end)
        mid = start
        a = entries[start].size / total
        b = a
        if w < h:
            while mid < end:
                aspect = self.normAspect(h, w, a, b)
                q = entries[mid].size / total
                if self.normAspect(h, w, a, b+q) > aspect:
                    break
                mid += 1
                b += q
            self.layoutBest(entries, start, mid, Rect(x, y, w, h*b))
            self.layout(entries, mid+1, end, Rect(x, y+h*b, w, h*(1-b)), True)
        else:
            while mid < end:
                aspect = self.normAspect(w, h, a, b)
                q = entries[mid].size/total
                if self.normAspect(w, h, a, b+q) > aspect:
                    break
                mid += 1
                b += q
            self.layoutBest(entries, start, mid, Rect(x, y, w*b, h))
            self.layout(entries, mid+1, end, Rect(x+w*b, y, w*(1-b), h), True)

    def aspect(self, big, small, a, b):
        return big*b/(small*a/b)

    def normAspect(self, big, small, a, b):
        x = self.aspect(big, small, a, b)
        if x < 1:
            return 1/x
        return x

if __name__ == '__main__':
    import random
    bounds = Rect(0, 0, 1, 1)
    alg = SquarifiedLayout()
    entries = []
    for i in range(20):
        entries.append(Entry(size=random.random()))
        print entries[-1].size
    sum = alg.totalSize(entries)
    #for entry in entries:
    #    entry.size /= sum
    alg.layout(entries, bounds=bounds)
    for entry in entries:
        print entry.bounds
