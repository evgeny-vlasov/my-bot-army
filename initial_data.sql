-- Add Andrew as first client
INSERT INTO clients (name, email, company_name, phone, status)
VALUES ('Andrew', 'andrew@keystonehardscapes.com', 'Keystone Hardscapes', NULL, 'active');

-- Add Keystone bot
INSERT INTO bots (client_id, bot_id, bot_name, port, status, config)
VALUES (
    1,
    'keystone-landscaping',
    'Keystone Hardscapes Assistant',
    5000,
    'active',
    '{"primary_color": "#2563eb", "position": "bottom-right"}'::jsonb
);

-- Add subscription
INSERT INTO subscriptions (
    client_id,
    plan_name,
    price,
    billing_cycle,
    status,
    current_period_start,
    current_period_end
)
VALUES (
    1,
    'testing',
    0.00,
    'monthly',
    'active',
    CURRENT_DATE,
    CURRENT_DATE + INTERVAL '1 month'
);
