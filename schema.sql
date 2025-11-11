-- Clients/Customers
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    company_name VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active'
);

-- Bots
CREATE TABLE bots (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    bot_id VARCHAR(100) UNIQUE NOT NULL,
    bot_name VARCHAR(255) NOT NULL,
    port INTEGER UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    config JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Subscriptions
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    plan_name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    billing_cycle VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    current_period_start DATE NOT NULL,
    current_period_end DATE NOT NULL,
    wave_invoice_id VARCHAR(255),
    last_paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Conversations
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    bot_id VARCHAR(100) REFERENCES bots(bot_id),
    session_id VARCHAR(255) NOT NULL,
    user_ip VARCHAR(50),
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    message_count INTEGER DEFAULT 0
);

-- Messages
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- API Usage
CREATE TABLE api_usage (
    id SERIAL PRIMARY KEY,
    bot_id VARCHAR(100) REFERENCES bots(bot_id),
    date DATE NOT NULL,
    requests INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cost DECIMAL(10,4) DEFAULT 0,
    UNIQUE(bot_id, date)
);

-- Invoices
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    due_date DATE NOT NULL,
    paid_at TIMESTAMP,
    wave_invoice_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Payments
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    invoice_id INTEGER REFERENCES invoices(id),
    wave_payment_id VARCHAR(255),
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50),
    paid_at TIMESTAMP DEFAULT NOW(),
    wave_fee DECIMAL(10,2)
);

-- Create indexes for better performance
CREATE INDEX idx_bots_client_id ON bots(client_id);
CREATE INDEX idx_conversations_bot_id ON conversations(bot_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_api_usage_bot_date ON api_usage(bot_id, date);
CREATE INDEX idx_subscriptions_client_id ON subscriptions(client_id);
