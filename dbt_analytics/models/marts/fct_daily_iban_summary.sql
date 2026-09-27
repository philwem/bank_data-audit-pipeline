select
    audit_date,
    country_code,
    count(*) as total_checks,
    count_if(is_valid = true) as valid_count,
    count_if(is_valid = false) as invalid_count,
    round(count_if(is_valid = true) * 100.0 / count(*), 2) as pass_rate_pct
from {{ ref('stg_iban_audit') }}
group by 1, 2
order by audit_date desc, total_checks desc
