"""Validation and presentation helpers for the raw-to-clean notebook walkthrough."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import textwrap
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import display, Markdown

from .acquisition import ROOT
from .snapshot_style import PAPER, INK, style_cell
from .eda import FEATURES, OUTCOMES
from .cleaning import US_STATES

from .conventions import MEASURES, KEYS, IDENTIFIERS, POSITIVE, PERCENTAGES
from .validation import cohort_reasons, build_analysis_cohort, assert_clean_cohort


def raw_snapshot(logical_id):
    catalog = json.loads((ROOT/'data/raw/catalog.json').read_text())
    record = catalog[logical_id]
    path = ROOT/record['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], 'Raw checksum mismatch'
    return path, record


def table_image(frames, labels, title, filename):
    """Compact 1920px PNG with measured row heights and no footer annotations."""
    rendered=[]; heights=[]
    for frame in frames:
        width=max(12,int(100/max(1,len(frame.columns))))
        def show(value):
            if pd.isna(value):return '<missing>'
            if isinstance(value,pd.Timestamp):return value.strftime('%Y-%m-%d')
            if isinstance(value,(float,np.floating)):return f'{value:,.2f}'.rstrip('0').rstrip('.')
            return textwrap.fill(str(value),width=width)
        rows=[[textwrap.fill(str(c).replace('_',' '),width=width) for c in frame.columns]]+frame.map(show).values.tolist()
        row_heights=[.16*max(s.count('\n')+1 for s in row)+.15 for row in rows]
        rendered.append(rows);heights.append(row_heights)
    title_lines=textwrap.fill(title,95)
    top=.2+.23*(title_lines.count('\n')+1)
    total=top+sum(sum(h)+.38 for h in heights)+.12
    fig=plt.figure(figsize=(12,total),facecolor=PAPER)
    fig.text(.02,1-.12/total,title_lines,va='top',fontsize=13,weight='bold',color=INK)
    cursor=top
    for rows,row_heights,label,color in zip(rendered,heights,labels,[INK]*len(frames)):
        fig.text(.02,1-(cursor+.07)/total,label,va='top',fontsize=10,weight='bold',color=color)
        cursor+=.34
        height=sum(row_heights)
        ax=fig.add_axes([.02,1-(cursor+height)/total,.96,height/total]);ax.axis('off')
        table=ax.table(cellText=rows,cellLoc='left',bbox=[0,0,1,1])
        table.auto_set_font_size(False);table.set_fontsize(9)
        for (row,col),cell in table.get_celld().items():
            cell.set_height(row_heights[row]/height)
            style_cell(cell, row)
        cursor+=height+.04
    path=ROOT/'reports/figures/cleaning'/filename
    path.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(path,dpi=160,facecolor=fig.get_facecolor(),pil_kwargs={'optimize':True})
    plt.show()
    return path


def comparison_image(raw, clean, title, filename, note=None):
    return table_image([raw,clean],['RAW EXCERPT','CLEANED EXCERPT'],title,filename)


def finish_chart(fig, filename, sentence_one, sentence_two, directory=None):
    """Save a captioned PNG and put exactly two explanatory sentences below notebook output."""
    caption=sentence_one+' '+sentence_two
    fig.tight_layout(rect=(0,.20,1,1))
    artist=fig.text(.04,.035,textwrap.fill(caption,115),fontsize=10,va='bottom')
    path=Path(directory or ROOT/'reports/analyses/exploration/figures')/filename
    path.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(path,dpi=160,bbox_inches='tight')
    artist.remove()
    fig.tight_layout()
    plt.show()
    display(Markdown(sentence_one+' '+sentence_two))
    return {'image':'reports/analyses/exploration/figures/'+filename,'caption':caption}
