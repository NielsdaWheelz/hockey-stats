"""finite detached territory evidence, support and accounting contracts."""

import math
import hashlib
import struct

from . import analysis_publication as p
from .artifacts import require

ROLES = ('exit_offense','entry_offense','zone_retention','entry_prevention')
ZONES = ('D','N','O')
AGES = (0,10,20,40,60,90)
REASONS = ('event_kind_unresolved','source_order_unresolved','clock_unresolved','orientation_unresolved',
    'conflicting_anchors','report_barrier_unresolved','membership_or_horizon_unavailable','identity_conflict',
    'strength_conflict','outside_five_on_five','period_or_game_end','restart_unproved','restart_clock_mismatch',
    'shift_endpoint_unresolved','shift_age_unavailable','zone_unavailable')


def _binding(value):
    p.fields(value,('uri','sha256'))
    p.text(value['uri'])
    p.digest(value['sha256'])


def _vector(value, length, *, probability=False, nonnegative=False, integer=False):
    require(type(value) is list and len(value)==length,'territory vector axes differ')
    for item in value:
        p.number(item,minimum=0 if probability or nonnegative else None,maximum=1 if probability else None,integer=integer)
    if probability:
        require(p.close(math.fsum(value),1),'territory distribution does not close')


def _coefficient(value, selected, year):
    p.fields(value,('status','current_season_information','prior_only','prior_kind','prior_anchor_season',
        'prior_seasons','likelihood_events','information_weight'))
    require(value['status'] in ('complete','failed','unavailable'),'invalid territory coefficient status')
    for key in ('current_season_information','prior_only'):
        require(type(value[key]) is bool and value[key]==selected[key],'territory role support flag differs')
    p.number(value['likelihood_events'],minimum=0,integer=True)
    p.number(value['information_weight'],minimum=0)
    require(value['current_season_information']==(value['information_weight']>0)
        and selected['events']==value['likelihood_events'] and selected['eligible_weight']==value['information_weight'],
        'territory role information differs')
    p.strings(value['prior_seasons'],ordered=True)
    require(value['prior_seasons']==selected['prior_seasons'],'territory role history differs')
    for prior in value['prior_seasons']:
        p.season(prior)
        require(prior<year,'territory future prior')
    if value['status']=='complete':
        require(value['prior_only']==(not value['current_season_information']),'territory prior-only differs')
        require((value['prior_kind']=='entry' and value['prior_anchor_season'] is None and not value['prior_seasons'])
            or (value['prior_kind']=='carry' and value['prior_seasons'] and value['prior_anchor_season']==value['prior_seasons'][-1]),
            'territory prior anchor differs')
    else:
        require(not value['prior_only'] and value['prior_kind'] is None and value['prior_anchor_season'] is None
            and not value['prior_seasons'],'incomplete territory role claims fitted history')


def reference_body(evidence, season, purpose, recipe_id):
    """the annual numerical reference excludes focal quantities and receipt cycles."""
    shift = evidence['shift_reference']['data']
    return dict(schema_tag='territory-evidence-v1-11-1',season=season,purpose=purpose,recipe_id=recipe_id,
        annual_state=evidence['annual_state'],prepared=evidence['prepared'],ev_state=evidence['successor_reference']['ev_state'],
        panel=evidence['successor_reference']['panel'],neutral_role_levels={role:{key:value for key,value in evidence['roles'][role].items()
            if key!='coefficient_support'} for role in ROLES},nuisance_coverage=evidence['nuisance_coverage'],
        common_shift_data=None if shift is None else {key:value for key,value in shift.items() if key not in ('focal_end_probabilities','end_difference')},
        successor_data=evidence['successor_reference']['data'])


def reference_digest(body):
    """canonical json with numeric leaves tagged by their exact binary64 bytes."""
    def canonical(value):
        if type(value) in (int,float):
            p.number(value)
            return ['f64',struct.pack('>d',0. if value==0 else float(value)).hex()]
        if type(value) is dict:
            return {key:canonical(item) for key,item in value.items()}
        if type(value) is list:
            return [canonical(item) for item in value]
        return value
    return hashlib.sha256(p.json_bytes(canonical(body))).hexdigest()


def validate_binding(data, row, catalogs, references):
    evidence = data['evidence']
    method = catalogs['method'][data['method_id']]
    require(method['family']=='territory' and method['recipe_id']=='territory-v1-11-1','territory method family/recipe differs')
    require(evidence['reference_id']==reference_digest(reference_body(evidence,row['season'],method['purpose'],method['recipe_id'])),
        'territory numerical reference digest differs')
    require(any(item['role']=='territory_reference' and item['sha256']==evidence['reference_id'] and item['seasons']==[row['season']]
        for item in method['inputs']) and any(item['sha256']==evidence['reference_id'] for item in method['evidence']),
        'territory method lacks numerical reference binding')
    bindings = [(role,evidence[key]) for role,key in (('annual_state','annual_state'),('prepared','prepared'))]
    bindings += [('ev_state',evidence['successor_reference']['ev_state']),('derivation',evidence['shift_reference']['receipt'])]
    if evidence['successor_reference']['panel'] is not None:
        bindings.append(('successor_panel',evidence['successor_reference']['panel']))
    for role,binding in bindings:
        require(binding in method['evidence'] and any(item['role']==role and item['sha256']==binding['sha256']
            and row['season'] in item['seasons'] for item in method['inputs']), 'territory method binding differs: '+role)
    require(all(year in method['fit_seasons'] for role in evidence['roles'].values()
        for year in role['coefficient_support']['prior_seasons']), 'territory prior outside method years')
    fixed = reference_body(evidence,row['season'],method['purpose'],method['recipe_id'])
    require(references.setdefault(('territory',row['season']),fixed)==fixed,'territory annual reference differs between players')


def validate(data, row):
    """validate published construction without reading source or numerical artifacts."""
    evidence = data['evidence']
    p.fields(evidence,('annual_state','prepared','reference_id','qualification_seconds','roles','nuisance_coverage',
        'shift_reference','successor_reference'))
    for key in ('annual_state','prepared'):
        _binding(evidence[key])
    p.digest(evidence['reference_id'])
    seconds = evidence['qualification_seconds']
    p.number(seconds,minimum=0)
    p.fields(evidence['roles'],ROLES)
    coefficients = []
    for role in ROLES:
        neutral = evidence['roles'][role]
        p.fields(neutral,('coefficient_support','neutral_hazard_per_second','neutral_one_second_probability'))
        selected = data[role]['support']
        require('territory' in selected['inferred_inputs'],'territory role inference is unmarked')
        _coefficient(neutral['coefficient_support'],selected,row['season'])
        coefficient = neutral['coefficient_support']
        coefficients.append(coefficient)
        require(selected['included_seconds']==seconds,'territory qualification is not known-path union time')
        complete = coefficient['status']=='complete'
        key = 'opponent_exit_hazard_per_second' if role=='zone_retention' else 'opponent_entry_hazard_per_second' if role=='entry_prevention' else 'hazard_per_second'
        for hazard, probability in ((neutral['neutral_hazard_per_second'],neutral['neutral_one_second_probability']),
                                    (data[role][key]['value'],data[role]['one_second_probability']['value'])):
            require((hazard is not None)==complete and (probability is not None)==complete,'territory role/head availability differs')
            if complete:
                p.number(hazard,minimum=0)
                require(hazard>0,'territory hazard must be positive')
                p.number(probability,minimum=0,maximum=1)
                expected = math.exp(-hazard) if role in ROLES[2:] else -math.expm1(-hazard)
                require(p.close(probability,expected),'territory conditional probability differs')
        for item in (data[role][key],data[role]['one_second_probability']):
            require(item['uncertainty']['kind']=='not_estimated','territory uncertainty is not estimated')
            if not complete:
                require(item['unavailable_reason']==('failed_fit' if coefficient['status']=='failed' else 'no_exposure'),
                    'territory role unavailable reason differs')
    for first,second in (('exit_offense','zone_retention'),('entry_offense','entry_prevention')):
        require(evidence['roles'][first]['neutral_hazard_per_second']==evidence['roles'][second]['neutral_hazard_per_second'],
            'territory neutral head differs between directions')
    support = data['support']
    require('territory' in support['inferred_inputs'],'territory inference is unmarked')
    require(support['included_seconds']==seconds and support['eligible_weight']==seconds
        and support['current_season_information']==all(c['current_season_information'] for c in coefficients)
        and support['prior_only']==all(c['status']=='complete' and c['prior_only'] for c in coefficients)
        and support['prior_seasons']==sorted({year for c in coefficients for year in c['prior_seasons']}),
        'territory aggregate support differs')
    require(max(c['likelihood_events'] for c in coefficients)<=support['events']<=sum(c['likelihood_events'] for c in coefficients),
        'territory distinct crossing union outside role counts')
    coverage = evidence['nuisance_coverage']
    durations = ('path_slot_seconds','terminal_carry_slot_seconds','whistle_risk_slot_seconds','live_end_risk_slot_seconds')
    counts = ('whistle_incidences','live_end_incidences','decidable_whistle_trials','ended_whistle_trials','restart_pairs','terminal_tails')
    p.fields(coverage,(*durations,*counts,'start_counts','on_the_fly_zone_counts','terminal_lag_seconds','censored_endpoints',
        'prior_only_cells','prior_only_restart_rows'))
    for key in durations:
        p.number(coverage[key],minimum=0)
        require(coverage[key]<=coverage['path_slot_seconds'] or p.close(coverage[key],coverage['path_slot_seconds']),
            'territory nuisance time exceeds path-slot time')
    for key in counts:
        p.number(coverage[key],minimum=0,integer=True)
    require(coverage['ended_whistle_trials']<=coverage['decidable_whistle_trials']<=coverage['whistle_incidences'],
        'territory whistle trial subsets differ')
    _vector(coverage['start_counts'],4,nonnegative=True,integer=True)
    _vector(coverage['on_the_fly_zone_counts'],3,nonnegative=True,integer=True)
    require(sum(coverage['on_the_fly_zone_counts'])==coverage['start_counts'][3],'territory live start mixture counts differ')
    lag = coverage['terminal_lag_seconds']
    require((lag is None)==(coverage['terminal_tails']==0),'territory terminal lag availability differs')
    if lag is not None:
        p.fields(lag,('p50','p90','p99','max'))
        for value in lag.values():
            p.number(value,minimum=0)
        require(lag['p50']<=lag['p90']<=lag['p99']<=lag['max'],'territory lag quantiles out of order')
    endpoints = coverage['censored_endpoints']
    require(type(endpoints) is list,'territory endpoints must be an array')
    for item in endpoints:
        p.fields(item,('reason','count'))
        require(item['reason'] in REASONS,'invalid territory endpoint reason')
        p.number(item['count'],minimum=0,integer=True)
    require([e['reason'] for e in endpoints]==sorted(set(e['reason'] for e in endpoints)),'duplicate/unordered territory endpoint reasons')
    cells = coverage['prior_only_cells']
    require(type(cells) is list,'territory prior cells must be an array')
    keys = []
    for item in cells:
        p.fields(item,('process','zone','age_lower'))
        require(item['process'] in ('w','d','h') and item['zone'] in ZONES and item['age_lower'] in AGES
            and type(item['age_lower']) is int,'invalid territory prior-only cell')
        keys.append((('w','d','h').index(item['process']),ZONES.index(item['zone']),AGES.index(item['age_lower'])))
    require(keys==sorted(set(keys)),'duplicate/unordered territory prior-only cells')
    restart_rows = coverage['prior_only_restart_rows']
    require(type(restart_rows) is list and restart_rows==[zone for zone in ZONES if zone in restart_rows],
        'invalid territory prior-only restart rows')
    shift, successor = evidence['shift_reference'],evidence['successor_reference']
    p.fields(shift,('available','reason','receipt','data'))
    p.fields(successor,('available','reason','ev_state','panel','data'))
    _binding(shift['receipt'])
    _binding(successor['ev_state'])
    if successor['panel'] is not None:
        _binding(successor['panel'])
    for reference in (shift,successor):
        require(type(reference['available']) is bool,'invalid territory reference availability')
        require(reference['data'] is not None and reference['reason'] is None if reference['available'] else
            reference['data'] is None and type(reference['reason']) is str and bool(reference['reason'].strip()),
            'territory reference availability/data/reason differs')
    require(not shift['available'] or all(c['status']=='complete' for c in coefficients),'territory shift reference lacks fitted heads')
    require(not successor['available'] or shift['available'] and successor['panel'] is not None,'territory successor lacks reference/panel')
    if shift['available']:
        require(min(coverage['whistle_risk_slot_seconds'],coverage['live_end_risk_slot_seconds'],coverage['decidable_whistle_trials'],
            coverage['restart_pairs'],sum(coverage['start_counts']))>0,'territory shift reference lacks observed support')
        ref = shift['data']
        p.fields(ref,('initial_start_probabilities','initial_on_the_fly_zone_probabilities','neutral_end_probabilities',
            'focal_end_probabilities','end_difference','neutral_occupancy_seconds','mean_shift_seconds','shifts_per_1000_minutes',
            'survival_at_90','tail_time_fraction'))
        for key in ('initial_start_probabilities','neutral_end_probabilities','focal_end_probabilities'):
            _vector(ref[key],4,probability=True)
        starts = coverage['start_counts']
        require(all(p.close(prob,count/sum(starts)) for prob,count in zip(ref['initial_start_probabilities'],starts,strict=True)),
            'territory initial frequencies differ from starts')
        mixture = ref['initial_on_the_fly_zone_probabilities']
        require((mixture is None)==(starts[3]==0),'territory live mixture availability differs')
        if mixture is not None:
            _vector(mixture,3,probability=True)
            require(all(p.close(prob,count/starts[3]) for prob,count in zip(mixture,coverage['on_the_fly_zone_counts'],strict=True)),
                'territory live mixture differs from starts')
        _vector(ref['end_difference'],4)
        require(p.close(math.fsum(ref['end_difference']),0) and all(p.close(d,f-n) for d,f,n in
            zip(ref['end_difference'],ref['focal_end_probabilities'],ref['neutral_end_probabilities'],strict=True)),
            'territory end probability difference does not close')
        _vector(ref['neutral_occupancy_seconds'],6,nonnegative=True)
        for seconds,width in zip(ref['neutral_occupancy_seconds'][:-1],(10,10,20,20,30),strict=True):
            require(seconds<=width+1e-9+width*1e-9,'territory finite occupancy exceeds bin width')
        for key in ('mean_shift_seconds','shifts_per_1000_minutes'):
            p.number(ref[key],minimum=0)
            require(ref[key]>0,'territory mean duration and workload must be positive')
        for key in ('survival_at_90','tail_time_fraction'):
            p.number(ref[key],minimum=0,maximum=1)
        require(p.close(math.fsum(ref['neutral_occupancy_seconds']),ref['mean_shift_seconds'])
            and p.close(ref['shifts_per_1000_minutes'],60000/ref['mean_shift_seconds'])
            and p.close(ref['tail_time_fraction'],ref['neutral_occupancy_seconds'][-1]/ref['mean_shift_seconds']),
            'territory reference duration/workload does not close')
    if successor['available']:
        ref = successor['data']
        p.fields(ref,('for_goals_per_shift','against_goals_per_shift','for_absolute_terms_goals_per_shift','against_absolute_terms_goals_per_shift'))
        for side,field in (('for','ice_won_goals_per_basket'),('against','ice_lost_goals_per_basket')):
            values = ref[side+'_goals_per_shift']
            scales = ref[side+'_absolute_terms_goals_per_shift']
            _vector(values,4)
            _vector(scales,4,nonnegative=True)
            require(all(abs(value)<=scale for value,scale in zip(values,scales,strict=True)),'territory successor exceeds absolute terms')
            d = shift['data']['end_difference']
            n0 = shift['data']['shifts_per_1000_minutes']
            expected = n0*math.fsum(weight*value for weight,value in zip(d,values,strict=True) if weight)
            actual = data[field]['value']
            allowance = 64*2**-52*n0*math.fsum(abs(weight)*scale for weight,scale in zip(d,scales,strict=True))
            require(math.isfinite(expected) and math.isfinite(allowance) and actual is not None
                and abs(actual-expected)<=1e-9+1e-9*max(abs(actual),abs(expected))+allowance,
                'territory basket value does not close with declared raw-term allowance')
    for field in ('ice_won_goals_per_basket','ice_lost_goals_per_basket'):
        estimate = data[field]
        require(estimate['uncertainty']['kind']=='not_estimated' and (estimate['value'] is not None)==successor['available'],
            'territory value prerequisite/uncertainty differs')
        if not successor['available']:
            reason = 'failed_fit' if any(c['status']=='failed' for c in coefficients) else 'no_exposure' if any(c['status']=='unavailable' for c in coefficients) else 'missing_source'
            require(estimate['unavailable_reason']==reason,'territory value unavailable reason differs')
