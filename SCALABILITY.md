# Scalability notes

Before going deeper into scalability, I want to clarify the current design.

For now, short-code generation is not deterministic: the same original URL is
looked up in the database and returns its existing code, but the code itself is
generated from time and a counter. I chose this because the short code should
be unique and stay at most 8 characters. A hash-based approach can give a
stable code, but avoiding collisions usually means using a longer value.

The current generator is inspired by a Snowflake ID, but it is not a full
Snowflake implementation. It uses a custom epoch at the start of 2026, a
timestamp, and a counter. Therefore, a machine whose clock is before that
epoch cannot generate an ID. It can generate up to 4,096 IDs in one second;
after that it rejects new requests for that second. It is suitable for one
instance, but it needs a change before running multiple instances.

## Question 1

If processing statistics or logs becomes slow, I would move that work out of
the redirect request. The main service can publish an event such as
`short_url_opened` to a message broker, then immediately continue with the
redirect. A separate worker can consume the event, write the detailed log, and
update a statistics table.

This removes extra logging and statistics work from the redirect path. The
trade-off is that statistics become eventually consistent: the count might be behind for a short time. The message broker and consumer should also
support retries, otherwise an event can be lost if the consumer is down.

## Question 2

The first practical step for multiple instances is to keep the URL-shortening
service stateless and run several copies behind a load balancer. The database and configuration must be external/shared dependencies; they
cannot stay inside one application instance.

At that point, the current ID generator is unsafe because two instances can
generate the same timestamp and counter. I would add bits for a unique worker/server ID. This increase the final code characters but I think we can deal with it until the result has not more than 10 characters. Worker IDs must
be assigned uniquely. Another option is to use a central ID generator or a
database sequence.

I would not split this small service into many microservices immediately. The
first useful split is statistics/logging, because it is already independent of
the redirect response. The shorten and redirect endpoints can stay together
and scale horizontally.

For a much larger system, the database can become the bottleneck. URL data can
be partitioned, and read replicas can help redirect lookups. However, this
adds operational complexity. Network failures, replica lag, duplicate event
delivery, and eventually consistent statistics all need to be handled. For
example, the statistics service can be behind the current redirect count for a
short time, so the product must accept that behavior.

## Question 3

For a heavy campaign, I would first protect the service at the edge with a
real rate limiter, ideally at the API gateway or reverse proxy. It can limit
requests per IP or client and return `429 Too Many Requests` before the
application or database becomes overloaded.

The current 4,096-ID-per-second limit also protects one instance by rejecting
extra shorten requests, but it is not a full rate limiter and it does not
protect the redirect endpoint. I would run multiple application instances
behind a load balancer and use a distributed rate-limit store so the limit is shared between instances.

For redirects, short code to original URL is mostly read-only data. Caching
that lookup can reduce database reads significantly during a campaign. Logging
and statistics should be sent asynchronously, as described above, so a spike
does not make every redirect wait for an extra database write. The database
still needs connection limits, monitoring, and alerts; otherwise adding more
application instances can simply move the overload to the database.
