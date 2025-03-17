from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from ..utils.py3 import range, zip

import matplotlib.collections as mcol
import matplotlib.colors as mcolors
import matplotlib.legend as mlegend
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import datetime
import mpld3
from .. import date2num, num2date

from .utils import shade_color


class CandlestickPlotHandler(object):
    legend_opens = [0.50, 0.50, 0.50]
    legend_highs = [1.00, 1.00, 1.00]
    legend_lows = [0.00, 0.00, 0.00]
    legend_closes = [0.80, 0.00, 1.00]

    def __init__(self,
                 ax, x, xlabel, opens, highs, lows, closes,
                 colorup='k', colordown='r',
                 edgeup=None, edgedown=None,
                 tickup=None, tickdown=None,
                 width=1, tickwidth=1,
                 edgeadjust=0.05, edgeshading=-10,
                 alpha=1.0,
                 label='_nolegend',
                 fillup=True,
                 filldown=True,
                 **kwargs):
        
 
        # Manager up/down bar colors
        r, g, b = mcolors.colorConverter.to_rgb(colorup)
        self.colorup = r, g, b, alpha
        r, g, b = mcolors.colorConverter.to_rgb(colordown)
        self.colordown = r, g, b, alpha
        # Manage the edge up/down colors for the bars
        if edgeup:
            r, g, b = mcolors.colorConverter.to_rgb(edgeup)
            self.edgeup = ((r, g, b, alpha),)
        else:
            self.edgeup = shade_color(self.colorup, edgeshading)

        if edgedown:
            r, g, b = mcolors.colorConverter.to_rgb(edgedown)
            self.edgedown = ((r, g, b, alpha),)
        else:
            self.edgedown = shade_color(self.colordown, edgeshading)

            # Manage the up/down tick colors
        if tickup:
            r, g, b = mcolors.colorConverter.to_rgb(tickup)
            self.tickup = ((r, g, b, alpha),)
        else:
            self.tickup = self.edgeup

        if tickdown:
            r, g, b = mcolors.colorConverter.to_rgb(tickdown)
            self.tickdown = ((r, g, b, alpha),)
        else:
            self.tickdown = self.edgedown

        self.barcol, self.tickcol = self.barcollection(
            xs=x, opens=opens, highs=highs, lows=lows, closes=closes,
            width=width, tickwidth=tickwidth, edgeadjust=edgeadjust, label=label, fillup=fillup, filldown=filldown,
            **kwargs)

        # add collections to the axis and return them
        ax.add_collection(self.tickcol)
        ax.add_collection(self.barcol)

        # Update the axis
        ax.update_datalim(((0, min(lows)), (len(opens), max(highs))))
        ax.autoscale_view()

        # Add self as legend handler for this object
        mlegend.Legend.update_default_handler_map({self.barcol: self})

    def legend_artist(self, legend, orig_handle, fontsize, handlebox):
        print('legend artist has been called ')
        x0 = 0
        y0 = handlebox.ydescent 
        width = handlebox.width / len(self.legend_opens)
        height = handlebox.height

        # Generate the x axis coordinates (handlebox based)
        xs = [x0 + width * (i + 0.5) for i in range(len(self.legend_opens))]
        barcol, tickcol = self.barcollection(
            xs,
            self.legend_opens, self.legend_highs,
            self.legend_lows, self.legend_closes,
            width=width, tickwidth=2,
            scaling=height, bot=y0)

        barcol.set_transform(handlebox.get_transform())
        handlebox.add_artist(barcol)
        tickcol.set_transform(handlebox.get_transform())
        handlebox.add_artist(tickcol)


        return barcol, tickcol

    def barcollection(self,
                      xs,
                      opens, highs, lows, closes,
                      width, tickwidth=1, edgeadjust=0,
                      label='_nolegend',
                      scaling=1.0, bot=0,
                      fillup=True, filldown=True,
                      **kwargs):
        print('barcollection has been called')
        # Prepack different zips of the series values
        oc = lambda: zip(opens, closes)  # NOQA: E731
        xoc = lambda: zip(xs, opens, closes)  # NOQA: E731
        iohlc = lambda: zip(xs, opens, highs, lows, closes)  # NOQA: E731

        colorup = self.colorup if fillup else 'None'
        colordown = self.colordown if filldown else 'None'
        colord = {True: colorup, False: colordown}
        colors = [colord[o < c] for o, c in oc()]

        edgecolord = {True: self.edgeup, False: self.edgedown}
        edgecolors = [edgecolord[o < c] for o, c in oc()]

        tickcolord = {True: self.tickup, False: self.tickdown}
        tickcolors = [tickcolord[o < c] for o, c in oc()]

        delta = width / 2 - edgeadjust
        # delta = date2num(datetime.timedelta(minutes=5)) 

        def barbox(i, open, close):
            # delta seen as closure
            left, right = i - delta, i + delta
            open = open * scaling + bot
            close = close * scaling + bot
            return (left, open), (left, close), (right, close), (right, open)

        barareas = [barbox(i, o, c) for i, o, c in xoc()]

        def tup(i, open, high, close):
            high = high * scaling + bot
            open = open * scaling + bot
            close = close * scaling + bot

            return (i, high), (i, max(open, close))

        tickrangesup = [tup(i, o, h, c) for i, o, h, l, c in iohlc()]

        def tdown(i, open, low, close):
            low = low * scaling + bot
            open = open * scaling + bot
            close = close * scaling + bot

            return (i, low), (i, min(open, close))

        tickrangesdown = [tdown(i, o, l, c) for i, o, h, l, c in iohlc()]

        # Extra variables for the collections
        useaa = 0,  # use tuple here
        lw = 0.5,   # and here
        tlw = tickwidth,

        # Bar collection for the candles
        barcol = mcol.PolyCollection(
            barareas,
            facecolors=colors,
            edgecolors=edgecolors,
            antialiaseds=useaa,
            linewidths=lw,
            label=label,
            **kwargs)

        # LineCollections have a higher zorder than PolyCollections
        # to ensure the edges of the bars are not overwriten by the Lines
        # we need to put the bars slightly over the LineCollections
        kwargs['zorder'] = barcol.get_zorder() * 0.9999

        # Up/down ticks from the body
        tickcol = mcol.LineCollection(
            tickrangesup + tickrangesdown,
            colors=tickcolors,
            linewidths=tlw,
            antialiaseds=useaa,
            **kwargs)

        # return barcol, tickcol
        return barcol, tickcol


def tf_plot_candlestick(ax, x, xlabel, opens, highs, lows, closes,
                     colorup='k', colordown='r',
                     edgeup=None, edgedown=None,
                     tickup=None, tickdown=None,
                     width=1, tickwidth=1.25,
                     edgeadjust=0.05, edgeshading=-10,
                     alpha=1.0,
                     label='_nolegend',
                     fillup=True,
                     filldown=True,
                     **kwargs):
    
    chandler = CandlestickPlotHandler(
        ax, x, xlabel, opens, highs, lows, closes,
        colorup, colordown,
        edgeup, edgedown,
        tickup, tickdown,
        width, tickwidth,
        edgeadjust, edgeshading,
        alpha,
        label,
        fillup,
        filldown,
        **kwargs)

    # Return the collections. the barcol goes first because
    # is the larger,  has the dominant zorder and defines the legend
    return chandler.barcol, chandler.tickcol