"""saved-only 04o tables, figures and bounded interpretation; no source reads or fits."""

import csv
import json
from pathlib import Path
import time

from hockey_stats.artifacts import (artifact,clean_implementation,json_values,load_arrays,
    require,resources,write_json)
from hockey_stats.chance_cli import identity,read_json


def _csv(root,name,rows):
    require(bool(rows),'context report table is empty: '+name)
    columns=list(dict.fromkeys(key for row in rows for key in row))
    with (root/name).open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
        writer.writerows({key:json.dumps(json_values(value),allow_nan=False,separators=(',',':'))
            if isinstance(value,(dict,list,tuple)) else json_values(value) for key,value in row.items()} for row in rows)
    return identity(root/name)


def _number(value):
    return 'unavailable' if value is None else f'{value:.6g}'


def _prediction_figure(root,d):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    schemes=('games','calendar_7_day','calendar_14_day')
    labels=('games','seven-day blocks','fourteen-day blocks')
    colors=('#126782','#d37a1c','#624080')
    panels=[('regional',['complete'],'complete regional loss; primary'),
            ('regional',['weighted_volume','shape','interaction'],'regional component accounting'),
            ('volume',['volume'],'scalar volume diagnostic'),
            ('native_inverse_share',['complete'],'native inverse-share diagnostic')]
    for ax,(metric,components,title) in zip(axes.flat,panels,strict=True):
        missing=set()
        for ci,component in enumerate(components):
            for si,scheme in enumerate(schemes):
                row=next(r for r in d['comparison_rows'] if r['variant']=='primary' and r['metric']==metric
                         and r['region']=='all' and r['component']==component and r['scheme']==scheme)
                y=ci+(si-1)*.18
                ax.plot(row['estimate'],y,'o',color=colors[si],markersize=5,label=labels[si] if ci==0 else None)
                if row['lower'] is not None:
                    ax.plot([row['lower'],row['upper']],[y,y],color=colors[si],linewidth=1.7)
                else:
                    missing.add(labels[si])
        if missing:
            ax.text(.02,.98,'unavailable intervals:\n'+', '.join(label for label in labels if label in missing),
                    transform=ax.transAxes,va='top',fontsize=7,wrap=True)
        ax.axvline(0.,color='#777777',linewidth=.8)
        ax.set_yticks(range(len(components)),[v.replace('_',' ') for v in components]);ax.invert_yaxis()
        ax.set_title(title,loc='left',fontsize=11)
        ax.set_xlabel('candidate − control; (recorded unblocked attempts/60)²',fontsize=8)
        ax.grid(axis='x',alpha=.18);ax.spines[['top','right']].set_visible(False)
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,frameon=False,fontsize=8,loc='outside lower center',ncols=3)
    fig.suptitle('lower loss is better; all three conditional 95% interval schemes',fontsize=13)
    fig.savefig(root/'prediction.png',dpi=170);plt.close(fig)
    return identity(root/'prediction.png')


def _player_figure(root,d):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    styles={'current':('o','#126782'),'carried_only':('x','#d37a1c'),'unseen':('+','#624080')}
    for ri,role in enumerate(('offense','defense')):
        for group,(marker,color) in styles.items():
            rows=[r for r in d['player_rows'] if r['role']==role and r['evidence_status']==group]
            for ci,metric in enumerate(('scalar_change','regional_change_size')):
                axes[ri,ci].scatter([r['training_included_minutes'] for r in rows],[r[metric] for r in rows],
                    s=14,alpha=.55,color=color,marker=marker,label=f'{group.replace("_"," ")} ({len(rows)})')
        yardstick=d['player_rows'][0]['scalar_practical_yardstick']
        axes[ri,0].axhline(0.,color='#777777',linewidth=.8)
        for sign in (-1,1): axes[ri,0].axhline(sign*yardstick,color='#777777',linewidth=.8,linestyle='--')
        for ci in range(2):
            ax=axes[ri,ci];ax.set_title(role+(': signed scalar change' if ci==0 else ': regional change size'),loc='left',fontsize=11)
            ax.set_xlabel('included final-training minutes',fontsize=9)
            ax.set_ylabel('recorded unblocked attempts/60',fontsize=9)
            ax.grid(alpha=.16);ax.spines[['top','right']].set_visible(False)
        axes[ri,1].legend(frameon=False,fontsize=8,loc='best')
    fig.suptitle('player point sensitivity in a common reference',fontsize=13)
    fig.supxlabel('dashed scalar lines: ±5% of training league rate, practical context only. prior-only rows at zero minutes are not new evidence.',fontsize=9)
    fig.savefig(root/'player-sensitivity.png',dpi=170);plt.close(fig)
    return identity(root/'player-sensitivity.png')


def report(assessment,output):
    """render only saved assessment fields/arrays; no input ledgers are required."""
    started=time.monotonic();path=Path(assessment).resolve(strict=True)
    d=read_json(path)
    require(d['kind']=='attribution_context_assessment' and d['schema_version']==1
            and d['purpose'] in ('research','fixture_exercise'), 'context report assessment schema differs')
    if d['purpose']=='research': clean_implementation(d['implementation'])
    arrays=load_arrays(d)
    variants=['primary',*(f'probe_{i:04b}' for i in range(1,16))]
    require(d['execution_status']=='complete' and d['variant_axes']==variants
        and d['inventory']['states']==20 and d['inventory']['new_states']==d['inventory']['reused_states']==10
        and len(d['probes'])==20 and len(d['comparison_rows'])==16*21*3
        and arrays['loss_numerators'].shape==(len(d['assessment_game_ids']),16,21)
        and arrays['player_scalar_changes'].shape==(16,2,d['inventory']['players'])
        and arrays['player_regional_changes'].shape==(16,2,d['inventory']['players'],12)
        and {(r['arm'],r['resolution']) for r in d['rate_rows']}==
            {(a,r) for a in ('candidate','control') for r in ('total','regional','native')}
        and len(d['player_rows'])==2*d['inventory']['players']
        and all(d['verification'][key]['status']=='verified'
                for key in ('heldout_rows','physical_prediction','control_comparisons','control_rate_diagnostics')),
        'context report requires complete saved assessment evidence')
    root=Path(output).absolute();require(not root.exists(),'report output already exists');root.mkdir(parents=True)
    comparison_rows=[dict(row,direction='zero_by_construction',interval_direction=row['direction'],
        interpretation='native volume/shape interaction is algebraically zero; numeric values and intervals are floating roundoff')
        if row['metric']=='native_inverse_share' and row['component']=='interaction' else row
        for row in d['comparison_rows']]
    region_columns={prefix+str(index):prefix+name for index,name in enumerate(d['region_names'])
        for prefix in ('candidate_region_','control_region_','region_change_')}
    tables={}
    for filename,key in (('comparison.csv','comparison_rows'),('game-losses.csv','game_rows'),
        ('player-changes.csv','player_rows'),('player-summary.csv','player_summary_rows'),
        ('player-probe-summary.csv','player_probe_summary_rows'),('rate-diagnostics.csv','rate_rows'),
        ('months.csv','month_rows'),('support.csv','support_rows')):
        rows=comparison_rows if key=='comparison_rows' else d[key]
        if key=='player_rows':
            rows=[{region_columns.get(name,name):value for name,value in row.items()} for row in rows]
        if key=='rate_rows':
            rows=[dict(row,**{'minimum_'+name:value for name,value in row['worst_location'].items()}) for row in rows]
        tables[filename]=_csv(root,filename,rows)
    figures=dict(prediction=_prediction_figure(root,d),player_sensitivity=_player_figure(root,d))
    primary=[r for r in comparison_rows if r['variant']=='primary']
    leading=[r for r in primary if r['metric']=='regional' and r['region']=='all' and r['component']=='complete']
    direction=d['primary_direction'];numerical=d['numerical_status']
    status=('fixture_verified' if d['purpose']=='fixture_exercise' else 'diagnosed') if numerical=='verified' else 'numerically_unresolved'
    introduction=('this fixture exercise uses explicitly synthetic counted histories. it verifies implementation contracts and makes no research recommendation.'
        if d['purpose']=='fixture_exercise' else
        'this is a research comparison of complete recorded unblocked-attempt rates. it does not admit a player-ability model. '
        'the response is source-locatable unblocked attempts on matched genuine 5v5 exposure, including zero-event time. '
        'all five selected seasons are research-exposed; the final-season split is '
        f"{d['coverage']['training_games']} training and {d['coverage']['assessment_games']} assessment games.")
    lines=['# 04o: score and game-time context','',introduction,'',
        f"the complete twelve-region prediction contrast is `{direction}`; candidate minus control is {_number(leading[0]['estimate'])} (recorded unblocked attempts/60)². lower is better.",'']
    for row in leading:
        lines.append(f"- {row['scheme']}: {_number(row['lower'])} to {_number(row['upper'])}; {row['undefined_draws']} unavailable draws.")
    lines.extend(['','other diagnostic directions (each combines all three interval schemes):',''])
    for row in primary:
        if (row['scheme']=='games' and row['region']=='all'
            and not (row['metric']=='regional' and row['component']=='complete')
            and not (row['metric']=='native_inverse_share' and row['component']=='interaction')):
            lines.append(f"- {row['metric']} {row['component']}: {_number(row['estimate'])}; `{row['direction']}`.")
    native={row['component']:row for row in primary if row['scheme']=='games'
        and row['metric']=='native_inverse_share' and row['region']=='all'}
    if (native['complete']['direction']=='supported_higher_loss' and native['shape']['estimate']>0
        and native['weighted_volume']['estimate']<0):
        lines.extend(['',f"the native inverse-share criterion supports higher complete loss for the candidate ({_number(native['complete']['estimate'])}). the increase is driven by shape, {_number(native['shape']['estimate'])} (`{native['shape']['direction']}`), partly offset by volume, {_number(native['weighted_volume']['estimate'])} (`{native['weighted_volume']['direction']}`)."])
    lines.extend(['','the native volume/shape interaction is zero by construction. its tiny saved values and interval endpoints are floating roundoff, not an unresolved scientific effect.'])
    supported_regions=[row for row in primary if row['scheme']=='games' and row['metric']=='regional'
        and row['region']!='all' and row['direction'] in ('supported_lower_loss','supported_higher_loss')]
    if supported_regions:
        lines.extend(['','individual-region supported directions are unadjusted descriptive comparisons across twelve regions. all twelve comparisons remain in the table; this adds no selection or adoption rule.',''])
        for row in supported_regions:
            lines.append(f"- {row['region']}: {_number(row['estimate'])} (recorded unblocked attempts/60)²; `{row['direction']}` across all three conditional interval schemes.")
    lines.extend(['','current-player point-change summaries, in recorded unblocked attempts/60:',''])
    for row in d['player_summary_rows']:
        lines.append(f"- {row['role']} {row['metric']}: exposure-weighted rms {_number(row['exposure_weighted_rms'])}; median {_number(row['median'])}; p90 {_number(row['p90'])}; maximum {_number(row['maximum'])}.")
    lines.extend(['','the intervals condition on fitted histories, selected scales, split, source population and this continuous working least-squares contrast. they are not absolute mse, equivalence evidence or calibrated player uncertainty.','',
        'the candidate retains home/away × period × clipped score intercepts. it adds shared home/away quadratic clock curves within each regulation period, with separate constant, leading and trailing magnitude terms. temporal shape uses forty fixed spatial modes; coarse context keeps native-cell maps. overtime has no added clock terms. curves need not join across intermissions; a quadratic cannot represent arbitrary abrupt late-game changes.','',
        'the fixed source support and assessment split come from the research-exposed 04n comparison. this is a bounded developmental comparison, not fresh prospective evidence. the score is partly created by players; adjustment changes the conditional decomposition and does not isolate their total causal contribution.','',
        'player sensitivity is a separate question. signed scalar changes and twelve regional complete-effect changes use the same final-training rate, exposure gauge and spatial reference in both arms. positive defense means more attempts allowed. current-player summaries use normalized training exposure; carried-only and unseen rows have zero training minutes and remain separately labeled. coefficient movement does not establish improved recovery.','',
        'the dashed scalar ±5% league-rate band supplies practical context. it is neither significance nor a spatial or adoption threshold. player coefficients receive no intervals or rank claims.','',
        'negative complete physical rates remain visible at total, regional and native resolutions. duration integrates strict negative intervals; mass is predicted attempts. player effects may be signed without making a complete physical rate valid. endpoint witnesses are one-sided exposure limits; isolated zeros carry no duration.',''])
    for row in d['rate_rows']:
        witness=row['worst_location']
        lines.append(f"- {row['arm']} {row['resolution']}: negative location-time fraction {_number(row['negative_location_time_fraction'])}; any-negative exposure {_number(row['any_negative_exposure_fraction'])}; negative mass {_number(row['negative_mass_predicted_attempts'])} predicted attempts; minimum/infimum {_number(row['minimum'])} attempts/60, `{witness['attainment']}` at game `{witness['game_id']}`, segment {witness['segment_index']}, {witness['side']}, period {witness['period']} clock {_number(witness['time'])}, location `{witness['location_label']}`.")
    rates={(row['arm'],row['resolution']):row for row in d['rate_rows']}
    for resolution in ('regional','native'):
        candidate,control=rates['candidate',resolution],rates['control',resolution]
        comparisons=[]
        for label,key,units in (('negative location-time fraction','negative_location_time_fraction',''),
            ('any-negative exposure fraction','any_negative_exposure_fraction',''),
            ('negative mass','negative_mass_predicted_attempts',' predicted attempts')):
            change='increases' if candidate[key]>control[key] else 'decreases' if candidate[key]<control[key] else 'is unchanged'
            comparisons.append(f"{label} {change} from {_number(control[key])} to {_number(candidate[key])}{units}")
        lines.extend(['',resolution+': '+'; '.join(comparisons)+'.'])
    lines.extend(['',f"numerical status: `{numerical}`. all sixteen final-component combinations preserve the primary direction: `{str(d['primary_direction_stable']).lower()}`. ten candidate states and ten exact control reuses retain twenty conditional probe receipts. endpoint and inherited scale limitations remain recorded in those receipts.",'',
        'adoption remains undecided. this study neither changes the observed website nor establishes chance valuation, player recovery or uncertainty calibration. no single next model revision is identified by this comparison.','',
        '[prediction figure](prediction.png) · [player sensitivity figure](player-sensitivity.png) · [comparison table](comparison.csv) · [player changes](player-changes.csv) · [rate diagnostics](rate-diagnostics.csv)',''])
    (root/'decision.md').write_text('\n'.join(lines))
    comparison_receipt=d['verification']['control_comparisons'];rate_receipt=d['verification']['control_rate_diagnostics']
    verification=['# verification','',f"assessment: `{identity(path)['sha256']}`",'',
        '- saved assessment and array hashes, finite axes, twenty-state/probe counts and sixteen variants checked.',
        '- held-out source rows reconcile counts and directed hours with saved grouped moments.',
        '- general-gram complete/volume/shape/interaction accounting closes, including common resampling draws and zero native interaction.',
        f"- frozen coarse controls: {comparison_receipt['metric_game_contractions']} metric-game contractions and {comparison_receipt['interval_comparisons']} interval rows; maximum absolute errors `{comparison_receipt['maximum_absolute_errors']}`. the original shared draw indices are reused.",
        f"- frozen constant-control diagnostics: {rate_receipt['frozen_rows']} resolutions; exact integer counts and witness identity; maximum absolute errors `{rate_receipt['maximum_absolute_errors']}`.",
        '- reports consume saved assessment evidence only; source ledgers and fit execution are not called.','',
        'the study verification record must additionally identify the independent implementation checks, figure inspection and final temporary-test deletion. software completion alone supplies no scientific admission.','']
    (root/'verification.md').write_text('\n'.join(verification))
    result=artifact('attribution_context_result',d['purpose'],dict(assessment=identity(path)),schema_version=1,
        execution_status='complete',numerical_status=numerical,study_status=status,
        nomination=None,admission='not_admitted',handoff=None,next_question=None,
        unresolved_reason=d['unresolved_reason'] or ('fixture exercise supplies no research recommendation'
            if d['purpose']=='fixture_exercise' else 'this diagnostic comparison does not uniquely identify the next model revision'),
        numerical_unresolved_reason=d['unresolved_reason'],prediction_direction=direction,
        primary_direction_stable=d['primary_direction_stable'],primary_comparison=primary,
        player_summaries=d['player_summary_rows'],rate_diagnostics=d['rate_rows'],
        coverage=d['coverage'],inventory=d['inventory'],verification=d['verification'],
        preparation_resources=d['preparation_resources'],fit_resources=d['fit_resources'],
        assessment_resources=d['resources'],tables=tables,figures=figures,limits=d['limits'],
        resources=dict(**resources(started),output_bytes=sum(path.stat().st_size for path in root.rglob('*') if path.is_file()),
            output_bytes_scope='tree before current manifest serialization'))
    write_json(root/'result.json',json_values(result))
    return identity(root/'result.json')
