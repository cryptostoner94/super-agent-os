from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter("apex_requests_total", "API requests received")
AGENT_RUNS    = Counter("apex_agent_runs_total", "agent invocations", ["agent"])
REVENUE_USD   = Counter("apex_revenue_usd_total", "revenue captured (USD)", ["agent","source"])
TASK_LATENCY  = Histogram("apex_task_latency_seconds", "end-to-end task latency")
ACTIVE_TASKS  = Gauge("apex_active_tasks", "tasks currently running", ["agent"])
