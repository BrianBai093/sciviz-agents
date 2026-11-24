# cell 65 | agent: analyst | original run: failed | artifacts created: none
script=script.replace('Average disruption percentile (0–100)','Mean disruption percentile (0–100)').replace('50th to below 90th (3,278)','Middle band (3,278)').replace('90th to 100th (887)','Top tenth (887)').replace('Met requirements /','Met rules /').replace('Lower rank with','Rank fell with').replace('from matplotlib.offsetbox import TextArea','from matplotlib.offsetbox import TextArea\nfrom matplotlib.table import Table\nfrom matplotlib.ticker import FixedFormatter')
a=script.index('                    for artist in model.findobj(Text):'); b=script.index('                return bbox',a)
script=script[:a]+'''                    for ax in model.axes:
                        formatter=ax.yaxis.get_major_formatter()
                        if parent=='P16':
                            formatter.func = lambda x, pos, original=formatter.func: new_word(parent, original(x,pos))
                    table_labels=[cell.get_text() for table in model.findobj(Table) for cell in table.get_celld().values()]
                    for artist in model.findobj(Text)+table_labels:
                        old=artist.get_text(); new=new_word(parent,old)
                        if new==old: continue
                        edits.append([old,new]); undo.append((artist,old)); anchor=artist.get_position()
                        artist.set_text(new); assert artist.get_position()==anchor
                        box=artist.get_window_extent(renderer).transformed(model.dpi_scale_trans.inverted())
                        if box.x0 < bbox.x0-.099 or box.x1 > bbox.x1+.099 or box.y0 < bbox.y0-.099 or box.y1 > bbox.y1+.099:
                            outside.append((new,list(box.bounds)))
                if mode.endswith('-hidden'):
                    for artist in model.findobj(Text)+[cell.get_text() for table in model.findobj(Table) for cell in table.get_celld().values()]: artist.set_alpha(0)
'''+script[b:]; rel=test_relabel()
