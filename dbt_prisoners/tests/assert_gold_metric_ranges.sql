select 'tournament_summary' as model_name
from {{ ref('tournament_summary') }}
where cooperation_rate < 0 or cooperation_rate > 1
   or defection_rate < 0 or defection_rate > 1

union all

select 'behavioral_drift' as model_name
from {{ ref('behavioral_drift') }}
where cooperation_rate < 0 or cooperation_rate > 1
   or defection_rate < 0 or defection_rate > 1

union all

select 'forgiveness_index' as model_name
from {{ ref('forgiveness_index') }}
where forgiveness_rate < 0 or forgiveness_rate > 1
