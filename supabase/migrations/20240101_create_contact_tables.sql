-- Create case counter table to track incremental case IDs
CREATE TABLE case_counter (
    id BIGINT PRIMARY KEY DEFAULT 1,
    last_case_id BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Insert initial record
INSERT INTO case_counter (id, last_case_id) VALUES (1, 0);

-- Create contact submissions table to store all contact form submissions
CREATE TABLE contact_submissions (
    id BIGSERIAL PRIMARY KEY,
    case_id BIGINT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    subject TEXT,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create indexes for better performance
CREATE INDEX idx_contact_submissions_case_id ON contact_submissions(case_id);
CREATE INDEX idx_contact_submissions_email ON contact_submissions(email);
CREATE INDEX idx_contact_submissions_created_at ON contact_submissions(created_at);

-- Add update trigger for case_counter
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_case_counter_updated_at BEFORE UPDATE ON case_counter
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 