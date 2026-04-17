# INT-003 Runtime SQL Checklist

This file is the operator SQL checklist for runtime integration checks.

Use it during:

- local integration
- export verification
- batch audit inspection
- smoke review with teammates

## 1. Check latest runtime batches

```sql
select id, run_id, profile_name, status, platforms, completed_at
from runtime_batch_runs
order by id desc
limit 10;
```

## 2. Check latest batch events

```sql
select id, run_id, event_type, platform, keyword, task_id, left(coalesce(message,''), 120) as message
from runtime_batch_run_events
order by id desc
limit 20;
```

## 3. Check latest crawl tasks

```sql
select id, keyword_id, platform, keyword, status, created_at, completed_at,
       config->>'task_dedup_key' as dedup_key
from crawl_tasks
order by id desc
limit 20;
```

## 4. Check one keyword's task history

```sql
select id, platform, keyword, status, created_at, completed_at,
       config->>'task_dedup_key' as dedup_key
from crawl_tasks
where keyword_id = <trend_keywords.id>
order by id desc;
```

## 5. Check cleaned outputs by task

```sql
select crawl_task_id, source_platform, keyword, count(*) as cleaned_count,
       max(created_at) as last_cleaned_at
from cleaned_trend_data
group by crawl_task_id, source_platform, keyword
order by crawl_task_id desc
limit 20;
```

## 6. Check latest trend_signal files

This one is file-based, not SQL:

```bash
find BeautyQA-TrendAgent/backend/data/trend_signal -type f | sort | tail -20
```

## 7. Check export handoff current files

```bash
find data/handoff/trend_signal/current -maxdepth 1 -type f | sort
```

## 8. Check task log for one task id

```sql
select task_id, level, message, created_at
from crawl_task_logs
where task_id = <crawl_task_id>
order by id desc
limit 50;
```

## 9. Check latest failed tasks

```sql
select id, platform, keyword, error_message, completed_at
from crawl_tasks
where status = 'failed'
order by completed_at desc
limit 20;
```

## 10. Minimal completion reading

Use these three questions:

1. did a batch run get created?
2. did tasks get scheduled and move status?
3. did cleaned rows and trend outputs appear?

If any answer is `no`, the runtime cycle is not complete.
