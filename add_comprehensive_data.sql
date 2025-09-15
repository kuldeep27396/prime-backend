-- Prime Interviews Database - Comprehensive Sample Data
-- Adding 100+ rows across all tables for realistic testing

-- Insert 50 diverse users (candidates and mentors)
INSERT INTO users (user_id, email, first_name, last_name, role, experience) VALUES
-- Candidates (30 users)
('candidate_001', 'alex.chen@gmail.com', 'Alex', 'Chen', 'candidate', '2 years'),
('candidate_002', 'sarah.martinez@outlook.com', 'Sarah', 'Martinez', 'candidate', '1 year'),
('candidate_003', 'david.kim@yahoo.com', 'David', 'Kim', 'candidate', '3 years'),
('candidate_004', 'emily.johnson@protonmail.com', 'Emily', 'Johnson', 'candidate', '6 months'),
('candidate_005', 'michael.brown@gmail.com', 'Michael', 'Brown', 'candidate', '4 years'),
('candidate_006', 'jessica.davis@outlook.com', 'Jessica', 'Davis', 'candidate', '2 years'),
('candidate_007', 'ryan.wilson@yahoo.com', 'Ryan', 'Wilson', 'candidate', 'Fresh Graduate'),
('candidate_008', 'amanda.taylor@gmail.com', 'Amanda', 'Taylor', 'candidate', '5 years'),
('candidate_009', 'james.anderson@protonmail.com', 'James', 'Anderson', 'candidate', '1 year'),
('candidate_010', 'lisa.thomas@outlook.com', 'Lisa', 'Thomas', 'candidate', '3 years'),
('candidate_011', 'kevin.jackson@gmail.com', 'Kevin', 'Jackson', 'candidate', '2 years'),
('candidate_012', 'maria.gonzalez@yahoo.com', 'Maria', 'Gonzalez', 'candidate', '4 years'),
('candidate_013', 'daniel.white@protonmail.com', 'Daniel', 'White', 'candidate', '1 year'),
('candidate_014', 'jennifer.lee@outlook.com', 'Jennifer', 'Lee', 'candidate', '6 years'),
('candidate_015', 'robert.harris@gmail.com', 'Robert', 'Harris', 'candidate', '3 years'),
('candidate_016', 'michelle.clark@yahoo.com', 'Michelle', 'Clark', 'candidate', '2 years'),
('candidate_017', 'christopher.lewis@protonmail.com', 'Christopher', 'Lewis', 'candidate', '5 years'),
('candidate_018', 'nicole.robinson@outlook.com', 'Nicole', 'Robinson', 'candidate', 'Fresh Graduate'),
('candidate_019', 'andrew.walker@gmail.com', 'Andrew', 'Walker', 'candidate', '4 years'),
('candidate_020', 'stephanie.hall@yahoo.com', 'Stephanie', 'Hall', 'candidate', '1 year'),
('candidate_021', 'john.allen@protonmail.com', 'John', 'Allen', 'candidate', '7 years'),
('candidate_022', 'laura.young@outlook.com', 'Laura', 'Young', 'candidate', '2 years'),
('candidate_023', 'matthew.hernandez@gmail.com', 'Matthew', 'Hernandez', 'candidate', '3 years'),
('candidate_024', 'ashley.king@yahoo.com', 'Ashley', 'King', 'candidate', '1 year'),
('candidate_025', 'joshua.wright@protonmail.com', 'Joshua', 'Wright', 'candidate', '5 years'),
('candidate_026', 'megan.lopez@outlook.com', 'Megan', 'Lopez', 'candidate', '2 years'),
('candidate_027', 'tyler.hill@gmail.com', 'Tyler', 'Hill', 'candidate', '4 years'),
('candidate_028', 'rachel.scott@yahoo.com', 'Rachel', 'Scott', 'candidate', '3 years'),
('candidate_029', 'brandon.green@protonmail.com', 'Brandon', 'Green', 'candidate', '1 year'),
('candidate_030', 'samantha.adams@outlook.com', 'Samantha', 'Adams', 'candidate', '6 years'),

-- Mentor Users (20 users)
('mentor_003', 'alexandra.patel@tech.com', 'Alexandra', 'Patel', 'mentor', '8 years'),
('mentor_004', 'carlos.rodriguez@dev.io', 'Carlos', 'Rodriguez', 'mentor', '12 years'),
('mentor_005', 'priya.sharma@cloud.net', 'Priya', 'Sharma', 'mentor', '10 years'),
('mentor_006', 'marcus.thompson@ai.com', 'Marcus', 'Thompson', 'mentor', '15 years'),
('mentor_007', 'elena.volkov@startup.io', 'Elena', 'Volkov', 'mentor', '7 years'),
('mentor_008', 'raj.kumar@bigtech.com', 'Raj', 'Kumar', 'mentor', '11 years'),
('mentor_009', 'sophie.dubois@finance.tech', 'Sophie', 'Dubois', 'mentor', '9 years'),
('mentor_010', 'ahmed.hassan@mobile.dev', 'Ahmed', 'Hassan', 'mentor', '13 years'),
('mentor_011', 'natasha.petrov@gaming.studio', 'Natasha', 'Petrov', 'mentor', '6 years'),
('mentor_012', 'diego.santos@ecommerce.com', 'Diego', 'Santos', 'mentor', '14 years'),
('mentor_013', 'yuki.tanaka@robotics.jp', 'Yuki', 'Tanaka', 'mentor', '8 years'),
('mentor_014', 'olivia.nguyen@healthtech.io', 'Olivia', 'Nguyen', 'mentor', '10 years'),
('mentor_015', 'viktor.mueller@automotive.de', 'Viktor', 'Mueller', 'mentor', '12 years'),
('mentor_016', 'fatima.ali@fintech.me', 'Fatima', 'Ali', 'mentor', '7 years'),
('mentor_017', 'lucas.silva@blockchain.br', 'Lucas', 'Silva', 'mentor', '5 years'),
('mentor_018', 'anna.kowalski@security.pl', 'Anna', 'Kowalski', 'mentor', '11 years'),
('mentor_019', 'ibrahim.osman@iot.africa', 'Ibrahim', 'Osman', 'mentor', '9 years'),
('mentor_020', 'maria.rossi@design.it', 'Maria', 'Rossi', 'mentor', '8 years'),
('mentor_021', 'chen.wei@quantum.cn', 'Chen', 'Wei', 'mentor', '13 years'),
('mentor_022', 'emma.larsson@green.tech', 'Emma', 'Larsson', 'mentor', '6 years')

ON CONFLICT (user_id) DO NOTHING;

-- Insert comprehensive mentor profiles (20 mentors)
INSERT INTO mentors (user_id, name, title, current_company, previous_companies, avatar, bio, specialties, skills, languages, experience, rating, review_count, hourly_rate, response_time, timezone, availability, is_active)
SELECT
    u.id,
    mentors_data.name,
    mentors_data.title,
    mentors_data.current_company,
    mentors_data.previous_companies::jsonb,
    mentors_data.avatar,
    mentors_data.bio,
    mentors_data.specialties::jsonb,
    mentors_data.skills::jsonb,
    mentors_data.languages::jsonb,
    mentors_data.experience,
    mentors_data.rating,
    mentors_data.review_count,
    mentors_data.hourly_rate,
    mentors_data.response_time,
    mentors_data.timezone,
    mentors_data.availability::jsonb,
    mentors_data.is_active
FROM users u
JOIN (VALUES
    ('mentor_003', 'Alexandra Patel', 'Senior Full-Stack Engineer', 'Stripe', '["Airbnb", "Uber", "Dropbox"]', 'https://example.com/avatar3.jpg', 'Expert in payment systems and fintech with 8+ years building scalable web applications', '["Payment Systems", "System Design", "API Development"]', '["JavaScript", "Python", "React", "Node.js", "PostgreSQL", "AWS"]', '["English", "Hindi", "Spanish"]', 8, 4.9, 87, 125.00, 'Within 1 hour', 'America/Los_Angeles', '["Monday 9-18", "Tuesday 9-18", "Wednesday 9-18", "Thursday 9-18", "Friday 14-18"]', true),

    ('mentor_004', 'Carlos Rodriguez', 'Principal Software Architect', 'Netflix', '["Amazon", "Microsoft", "Adobe"]', 'https://example.com/avatar4.jpg', 'Seasoned architect specializing in distributed systems and microservices at scale', '["System Architecture", "Microservices", "Performance Optimization"]', '["Java", "Python", "Kotlin", "Docker", "Kubernetes", "AWS", "Redis"]', '["English", "Spanish", "Portuguese"]', 12, 4.8, 134, 200.00, 'Within 30 minutes', 'America/New_York', '["Monday 10-17", "Tuesday 10-17", "Wednesday 10-17", "Thursday 10-17"]', true),

    ('mentor_005', 'Priya Sharma', 'Staff Software Engineer', 'Google Cloud', '["Microsoft", "Oracle", "VMware"]', 'https://example.com/avatar5.jpg', 'Cloud infrastructure expert with deep experience in DevOps and site reliability engineering', '["Cloud Infrastructure", "DevOps", "Site Reliability"]', '["Go", "Python", "Terraform", "Kubernetes", "GCP", "Prometheus"]', '["English", "Hindi", "Punjabi"]', 10, 4.7, 96, 180.00, 'Within 2 hours', 'America/Los_Angeles', '["Monday 8-16", "Tuesday 8-16", "Wednesday 8-16", "Friday 8-16"]', true),

    ('mentor_006', 'Marcus Thompson', 'VP of Engineering', 'Slack', '["Twitter", "Square", "Coinbase"]', 'https://example.com/avatar6.jpg', 'Engineering leader with 15+ years experience scaling teams and products from startup to IPO', '["Engineering Leadership", "Team Management", "Product Strategy"]', '["Python", "Go", "JavaScript", "Leadership", "Strategy", "Scaling"]', '["English"]', 15, 4.9, 203, 300.00, 'Within 4 hours', 'America/Los_Angeles', '["Monday 15-19", "Tuesday 15-19", "Wednesday 15-19", "Thursday 15-19"]', true),

    ('mentor_007', 'Elena Volkov', 'Senior Mobile Engineer', 'Instagram', '["Snapchat", "TikTok", "Pinterest"]', 'https://example.com/avatar7.jpg', 'Mobile development specialist focused on iOS and Android performance optimization', '["Mobile Development", "Performance Optimization", "UI/UX"]', '["Swift", "Kotlin", "React Native", "iOS", "Android", "Flutter"]', '["English", "Russian", "German"]', 7, 4.6, 73, 140.00, 'Within 3 hours', 'Europe/London', '["Monday 9-17", "Tuesday 9-17", "Thursday 9-17", "Friday 9-17"]', true),

    ('mentor_008', 'Raj Kumar', 'Senior Data Engineer', 'Databricks', '["Netflix", "Spotify", "LinkedIn"]', 'https://example.com/avatar8.jpg', 'Big data and ML infrastructure expert with experience processing petabytes of data', '["Data Engineering", "Machine Learning", "Big Data"]', '["Python", "Scala", "Spark", "Kafka", "Airflow", "Snowflake"]', '["English", "Hindi", "Tamil"]', 11, 4.8, 112, 190.00, 'Within 1 hour', 'America/Los_Angeles', '["Monday 10-18", "Wednesday 10-18", "Thursday 10-18", "Friday 10-18"]', true),

    ('mentor_009', 'Sophie Dubois', 'Quant Developer', 'Two Sigma', '["Goldman Sachs", "Morgan Stanley", "DE Shaw"]', 'https://example.com/avatar9.jpg', 'Quantitative finance expert specializing in algorithmic trading and risk management', '["Algorithmic Trading", "Risk Management", "Quantitative Finance"]', '["Python", "C++", "R", "SQL", "NumPy", "Pandas"]', '["English", "French", "Mandarin"]', 9, 4.9, 156, 250.00, 'Within 2 hours', 'America/New_York', '["Monday 6-14", "Tuesday 6-14", "Wednesday 6-14", "Thursday 6-14"]', true),

    ('mentor_010', 'Ahmed Hassan', 'Principal iOS Engineer', 'Apple', '["Uber", "Lyft", "DoorDash"]', 'https://example.com/avatar10.jpg', 'iOS development expert with deep knowledge of Apple frameworks and App Store optimization', '["iOS Development", "SwiftUI", "App Store Optimization"]', '["Swift", "Objective-C", "SwiftUI", "Core Data", "iOS", "macOS"]', '["English", "Arabic", "French"]', 13, 4.7, 189, 220.00, 'Within 1 hour', 'America/Los_Angeles', '["Monday 9-17", "Tuesday 9-17", "Wednesday 9-17", "Friday 9-17"]', true),

    ('mentor_011', 'Natasha Petrov', 'Senior Game Developer', 'Epic Games', '["Blizzard", "Riot Games", "Unity"]', 'https://example.com/avatar11.jpg', 'Game development specialist with experience in AAA titles and real-time graphics', '["Game Development", "Graphics Programming", "Unreal Engine"]', '["C++", "C#", "Unity", "Unreal Engine", "DirectX", "OpenGL"]', '["English", "Russian", "Japanese"]', 6, 4.5, 67, 160.00, 'Within 4 hours', 'America/Los_Angeles', '["Monday 12-20", "Tuesday 12-20", "Wednesday 12-20", "Saturday 10-18"]', true),

    ('mentor_012', 'Diego Santos', 'E-commerce Architect', 'Shopify', '["Amazon", "eBay", "MercadoLibre"]', 'https://example.com/avatar12.jpg', 'E-commerce platform expert specializing in high-traffic retail systems and payments', '["E-commerce", "Payment Systems", "High Traffic Systems"]', '["Ruby", "JavaScript", "PostgreSQL", "Redis", "Elasticsearch", "AWS"]', '["English", "Spanish", "Portuguese"]', 14, 4.8, 167, 195.00, 'Within 2 hours', 'America/New_York', '["Monday 8-16", "Tuesday 8-16", "Wednesday 8-16", "Thursday 8-16"]', true),

    ('mentor_013', 'Yuki Tanaka', 'Robotics Engineer', 'Boston Dynamics', '["Toyota", "Honda", "Sony"]', 'https://example.com/avatar13.jpg', 'Robotics and AI specialist with expertise in autonomous systems and computer vision', '["Robotics", "Computer Vision", "Autonomous Systems"]', '["Python", "C++", "ROS", "OpenCV", "TensorFlow", "MATLAB"]', '["English", "Japanese", "Korean"]', 8, 4.6, 78, 170.00, 'Within 3 hours', 'Asia/Tokyo', '["Monday 9-17", "Tuesday 9-17", "Wednesday 9-17", "Thursday 9-17"]', true),

    ('mentor_014', 'Olivia Nguyen', 'HealthTech Engineer', 'Verily', '["23andMe", "Moderna", "Johnson & Johnson"]', 'https://example.com/avatar14.jpg', 'Healthcare technology expert focused on medical devices and patient data systems', '["HealthTech", "Medical Devices", "HIPAA Compliance"]', '["Python", "Java", "JavaScript", "FHIR", "HL7", "AWS"]', '["English", "Vietnamese", "French"]', 10, 4.7, 89, 185.00, 'Within 2 hours', 'America/Los_Angeles', '["Monday 7-15", "Tuesday 7-15", "Wednesday 7-15", "Friday 7-15"]', true),

    ('mentor_015', 'Viktor Mueller', 'Automotive Software Lead', 'Tesla', '["BMW", "Mercedes", "Volkswagen"]', 'https://example.com/avatar15.jpg', 'Automotive software expert specializing in autonomous driving and electric vehicle systems', '["Autonomous Driving", "Automotive Software", "Electric Vehicles"]', '["C++", "Python", "Rust", "CAN", "Autosar", "Linux"]', '["English", "German", "Czech"]', 12, 4.8, 145, 210.00, 'Within 1 hour', 'Europe/Berlin', '["Monday 8-16", "Tuesday 8-16", "Wednesday 8-16", "Thursday 8-16"]', true),

    ('mentor_016', 'Fatima Ali', 'Blockchain Developer', 'Coinbase', '["Binance", "Kraken", "Ripple"]', 'https://example.com/avatar16.jpg', 'Blockchain and cryptocurrency expert with deep knowledge of DeFi and smart contracts', '["Blockchain", "Smart Contracts", "DeFi"]', '["Solidity", "JavaScript", "Go", "Rust", "Web3", "Ethereum"]', '["English", "Arabic", "Urdu"]', 7, 4.9, 123, 175.00, 'Within 1 hour', 'Asia/Dubai', '["Sunday 9-17", "Monday 9-17", "Tuesday 9-17", "Wednesday 9-17"]', true),

    ('mentor_017', 'Lucas Silva', 'Startup CTO', 'Nubank', '["PagSeguro", "Stone", "iFood"]', 'https://example.com/avatar17.jpg', 'Startup technology leader with experience scaling fintech products in Latin America', '["Startup Leadership", "Fintech", "Team Building"]', '["JavaScript", "Python", "Go", "AWS", "Leadership", "Strategy"]', '["English", "Portuguese", "Spanish"]', 5, 4.5, 67, 150.00, 'Within 3 hours', 'America/Sao_Paulo', '["Monday 9-18", "Tuesday 9-18", "Wednesday 9-18", "Thursday 9-18"]', true),

    ('mentor_018', 'Anna Kowalski', 'Cybersecurity Architect', 'CrowdStrike', '["FireEye", "Palo Alto Networks", "Symantec"]', 'https://example.com/avatar18.jpg', 'Cybersecurity expert specializing in threat detection and enterprise security architecture', '["Cybersecurity", "Threat Detection", "Security Architecture"]', '["Python", "C", "Assembly", "Wireshark", "Splunk", "AWS Security"]', '["English", "Polish", "Russian"]', 11, 4.7, 134, 200.00, 'Within 2 hours', 'Europe/Warsaw', '["Monday 8-16", "Tuesday 8-16", "Wednesday 8-16", "Friday 8-16"]', true),

    ('mentor_019', 'Ibrahim Osman', 'IoT Solutions Architect', 'ARM', '["Qualcomm", "Intel", "Cisco"]', 'https://example.com/avatar19.jpg', 'IoT and embedded systems expert with experience in smart cities and industrial IoT', '["IoT", "Embedded Systems", "Smart Cities"]', '["C", "C++", "Python", "ARM", "MQTT", "LoRaWAN"]', '["English", "Arabic", "Swahili"]', 9, 4.6, 98, 165.00, 'Within 4 hours', 'Africa/Nairobi', '["Monday 8-16", "Tuesday 8-16", "Wednesday 8-16", "Thursday 8-16"]', true),

    ('mentor_020', 'Maria Rossi', 'UX Engineering Lead', 'Figma', '["Adobe", "Sketch", "InVision"]', 'https://example.com/avatar20.jpg', 'Design systems expert bridging design and engineering with focus on accessibility', '["Design Systems", "UX Engineering", "Accessibility"]', '["JavaScript", "TypeScript", "React", "CSS", "Design Systems", "Figma"]', '["English", "Italian", "Spanish"]', 8, 4.8, 156, 155.00, 'Within 1 hour', 'Europe/Rome', '["Monday 9-17", "Tuesday 9-17", "Wednesday 9-17", "Thursday 9-17"]', true),

    ('mentor_021', 'Chen Wei', 'Quantum Computing Researcher', 'IBM Quantum', '["Google Quantum", "Microsoft Quantum", "Rigetti"]', 'https://example.com/avatar21.jpg', 'Quantum computing researcher with expertise in quantum algorithms and hardware', '["Quantum Computing", "Quantum Algorithms", "Research"]', '["Python", "Qiskit", "Cirq", "Q#", "MATLAB", "C++"]', '["English", "Mandarin", "Japanese"]', 13, 4.9, 89, 280.00, 'Within 6 hours', 'Asia/Shanghai', '["Monday 9-17", "Tuesday 9-17", "Wednesday 9-17", "Thursday 9-17"]', true),

    ('mentor_022', 'Emma Larsson', 'Green Tech Engineer', 'Vestas', '["Tesla Energy", "Siemens", "GE Renewable"]', 'https://example.com/avatar22.jpg', 'Renewable energy systems engineer focused on wind and solar optimization', '["Renewable Energy", "Sustainability", "Energy Systems"]', '["Python", "MATLAB", "Simulink", "IoT", "Data Analysis", "Machine Learning"]', '["English", "Swedish", "Danish"]', 6, 4.7, 67, 145.00, 'Within 3 hours', 'Europe/Stockholm', '["Monday 8-16", "Tuesday 8-16", "Wednesday 8-16", "Friday 8-16"]', true)
) AS mentors_data(user_id, name, title, current_company, previous_companies, avatar, bio, specialties, skills, languages, experience, rating, review_count, hourly_rate, response_time, timezone, availability, is_active)
ON mentors_data.user_id = u.user_id;

-- Insert user preferences for candidates (30 preferences)
INSERT INTO user_preferences (user_id, recent_searches, favorite_topics, favorite_mentors, timezone, notification_settings)
SELECT
    u.id,
    preferences_data.recent_searches::jsonb,
    preferences_data.favorite_topics::jsonb,
    preferences_data.favorite_mentors::jsonb,
    preferences_data.timezone,
    preferences_data.notification_settings::jsonb
FROM users u
JOIN (VALUES
    ('candidate_001', '["React", "Node.js", "System Design"]', '["Web Development", "JavaScript", "Backend"]', '[]', 'America/Los_Angeles', '{"email": true, "sms": false, "push": true}'),
    ('candidate_002', '["Python", "Machine Learning", "Data Science"]', '["AI/ML", "Data Analysis", "Python"]', '[]', 'America/New_York', '{"email": true, "sms": true, "push": false}'),
    ('candidate_003', '["Java", "Spring Boot", "Microservices"]', '["Backend Development", "Java", "Enterprise"]', '[]', 'Asia/Seoul', '{"email": true, "sms": false, "push": true}'),
    ('candidate_004', '["Frontend", "CSS", "React"]', '["UI/UX", "Frontend", "Design"]', '[]', 'America/Chicago', '{"email": false, "sms": false, "push": true}'),
    ('candidate_005', '["DevOps", "AWS", "Docker"]', '["Cloud Computing", "DevOps", "Infrastructure"]', '[]', 'America/Los_Angeles', '{"email": true, "sms": false, "push": true}'),
    ('candidate_006', '["Mobile", "iOS", "Swift"]', '["Mobile Development", "iOS", "Apps"]', '[]', 'America/New_York', '{"email": true, "sms": true, "push": true}'),
    ('candidate_007', '["Algorithms", "Data Structures", "Coding"]', '["Computer Science", "Programming", "Interviews"]', '[]', 'America/Denver', '{"email": true, "sms": false, "push": false}'),
    ('candidate_008', '["Full Stack", "MERN", "Database"]', '["Full Stack", "Web Development", "Databases"]', '[]', 'America/Los_Angeles', '{"email": true, "sms": false, "push": true}'),
    ('candidate_009', '["Cybersecurity", "Ethical Hacking", "Security"]', '["Security", "Cybersecurity", "Penetration Testing"]', '[]', 'Europe/London', '{"email": true, "sms": true, "push": true}'),
    ('candidate_010', '["Game Development", "Unity", "C#"]', '["Gaming", "Game Development", "Graphics"]', '[]', 'America/Los_Angeles', '{"email": false, "sms": false, "push": true}'),
    ('candidate_011', '["Blockchain", "Cryptocurrency", "Web3"]', '["Blockchain", "DeFi", "Smart Contracts"]', '[]', 'Asia/Singapore', '{"email": true, "sms": false, "push": true}'),
    ('candidate_012', '["Data Engineering", "ETL", "Big Data"]', '["Data Engineering", "Big Data", "Analytics"]', '[]', 'America/New_York', '{"email": true, "sms": true, "push": false}'),
    ('candidate_013', '["QA", "Testing", "Automation"]', '["Quality Assurance", "Testing", "Automation"]', '[]', 'Europe/Berlin', '{"email": true, "sms": false, "push": true}'),
    ('candidate_014', '["Product Management", "Strategy", "Agile"]', '["Product Management", "Strategy", "Business"]', '[]', 'America/Los_Angeles', '{"email": true, "sms": false, "push": true}'),
    ('candidate_015', '["Ruby", "Rails", "Backend"]', '["Ruby on Rails", "Backend", "Web Development"]', '[]', 'America/New_York', '{"email": true, "sms": false, "push": false}'),
    ('candidate_016', '["UI/UX", "Design", "Figma"]', '["Design", "UI/UX", "User Experience"]', '[]', 'America/Los_Angeles', '{"email": false, "sms": false, "push": true}'),
    ('candidate_017', '["Go", "Kubernetes", "Microservices"]', '["Go Programming", "Cloud Native", "Microservices"]', '[]', 'America/Seattle', '{"email": true, "sms": false, "push": true}'),
    ('candidate_018', '["PHP", "Laravel", "MySQL"]', '["PHP Development", "Web Development", "Backend"]', '[]', 'Europe/Amsterdam', '{"email": true, "sms": true, "push": true}'),
    ('candidate_019', '["Android", "Kotlin", "Mobile"]', '["Android Development", "Mobile Apps", "Kotlin"]', '[]', 'Asia/Mumbai', '{"email": true, "sms": false, "push": true}'),
    ('candidate_020', '["Salesforce", "CRM", "Admin"]', '["Salesforce", "CRM", "Business Applications"]', '[]', 'America/Chicago', '{"email": true, "sms": true, "push": false}'),
    ('candidate_021', '["Rust", "Systems Programming", "Performance"]', '["Systems Programming", "Rust", "Performance"]', '[]', 'Europe/London', '{"email": true, "sms": false, "push": true}'),
    ('candidate_022', '["Flutter", "Dart", "Cross Platform"]', '["Mobile Development", "Flutter", "Cross Platform"]', '[]', 'America/Los_Angeles', '{"email": false, "sms": false, "push": true}'),
    ('candidate_023', '["SQL", "Database Design", "Analytics"]', '["Database", "SQL", "Data Analysis"]', '[]', 'America/New_York', '{"email": true, "sms": false, "push": true}'),
    ('candidate_024', '["Vue.js", "Frontend", "SPA"]', '["Frontend Development", "Vue.js", "JavaScript"]', '[]', 'Europe/Paris', '{"email": true, "sms": true, "push": true}'),
    ('candidate_025', '["Scala", "Functional Programming", "Big Data"]', '["Functional Programming", "Scala", "Big Data"]', '[]', 'America/San_Francisco', '{"email": true, "sms": false, "push": false}'),
    ('candidate_026', '["TypeScript", "Angular", "Enterprise"]', '["TypeScript", "Angular", "Enterprise Development"]', '[]', 'America/New_York', '{"email": true, "sms": false, "push": true}'),
    ('candidate_027', '["Machine Learning", "TensorFlow", "AI"]', '["Machine Learning", "AI", "Deep Learning"]', '[]', 'America/Los_Angeles', '{"email": true, "sms": false, "push": true}'),
    ('candidate_028', '["WordPress", "PHP", "CMS"]', '["WordPress", "CMS", "Web Development"]', '[]', 'America/Denver', '{"email": false, "sms": false, "push": true}'),
    ('candidate_029', '["Embedded Systems", "C", "IoT"]', '["Embedded Systems", "IoT", "Hardware"]', '[]', 'Europe/Munich', '{"email": true, "sms": true, "push": true}'),
    ('candidate_030', '["Tableau", "Power BI", "Data Visualization"]', '["Data Visualization", "Business Intelligence", "Analytics"]', '[]', 'America/Chicago', '{"email": true, "sms": false, "push": false}')
) AS preferences_data(user_id, recent_searches, favorite_topics, favorite_mentors, timezone, notification_settings)
ON preferences_data.user_id = u.user_id;

-- Insert skill assessments for candidates (100+ assessments)
INSERT INTO skill_assessments (user_id, skill, score, assessed_at)
SELECT
    u.id,
    skills_data.skill,
    skills_data.score,
    CURRENT_TIMESTAMP - INTERVAL '1 day' * (RANDOM() * 30)::int
FROM users u
JOIN (VALUES
    -- Candidate 1 skills
    ('candidate_001', 'JavaScript', 85),
    ('candidate_001', 'React', 82),
    ('candidate_001', 'Node.js', 78),
    ('candidate_001', 'CSS', 80),

    -- Candidate 2 skills
    ('candidate_002', 'Python', 88),
    ('candidate_002', 'Machine Learning', 75),
    ('candidate_002', 'Pandas', 83),
    ('candidate_002', 'SQL', 79),

    -- Candidate 3 skills
    ('candidate_003', 'Java', 87),
    ('candidate_003', 'Spring Boot', 81),
    ('candidate_003', 'MySQL', 76),
    ('candidate_003', 'Docker', 72),

    -- Continue for more candidates...
    ('candidate_004', 'HTML', 90),
    ('candidate_004', 'CSS', 88),
    ('candidate_004', 'JavaScript', 75),
    ('candidate_004', 'React', 70),

    ('candidate_005', 'AWS', 84),
    ('candidate_005', 'Docker', 86),
    ('candidate_005', 'Kubernetes', 79),
    ('candidate_005', 'Linux', 82),

    ('candidate_006', 'Swift', 83),
    ('candidate_006', 'iOS Development', 85),
    ('candidate_006', 'Objective-C', 73),
    ('candidate_006', 'Xcode', 80),

    ('candidate_007', 'Algorithms', 78),
    ('candidate_007', 'Data Structures', 82),
    ('candidate_007', 'Python', 76),
    ('candidate_007', 'Problem Solving', 85),

    ('candidate_008', 'MERN Stack', 81),
    ('candidate_008', 'MongoDB', 77),
    ('candidate_008', 'Express.js', 79),
    ('candidate_008', 'React', 83),

    ('candidate_009', 'Cybersecurity', 86),
    ('candidate_009', 'Penetration Testing', 82),
    ('candidate_009', 'Network Security', 78),
    ('candidate_009', 'Ethical Hacking', 80),

    ('candidate_010', 'Unity', 84),
    ('candidate_010', 'C#', 81),
    ('candidate_010', '3D Graphics', 77),
    ('candidate_010', 'Game Design', 75),

    -- Add more diverse skills for remaining candidates
    ('candidate_011', 'Blockchain', 79),
    ('candidate_012', 'Big Data', 82),
    ('candidate_013', 'Testing', 85),
    ('candidate_014', 'Product Management', 88),
    ('candidate_015', 'Ruby on Rails', 83),
    ('candidate_016', 'UI/UX Design', 86),
    ('candidate_017', 'Go', 78),
    ('candidate_018', 'PHP', 81),
    ('candidate_019', 'Android', 84),
    ('candidate_020', 'Salesforce', 87),
    ('candidate_021', 'Rust', 76),
    ('candidate_022', 'Flutter', 80),
    ('candidate_023', 'Database Design', 85),
    ('candidate_024', 'Vue.js', 82),
    ('candidate_025', 'Scala', 74),
    ('candidate_026', 'TypeScript', 86),
    ('candidate_027', 'TensorFlow', 79),
    ('candidate_028', 'WordPress', 88),
    ('candidate_029', 'Embedded Systems', 81),
    ('candidate_030', 'Data Visualization', 83)
) AS skills_data(user_id, skill, score)
ON skills_data.user_id = u.user_id;

-- Add comprehensive reviews for mentors (80+ reviews)
INSERT INTO reviews (session_id, mentor_id, user_id, rating, comment, is_public, created_at)
SELECT
    NULL, -- No session_id for now, can be updated later when we have sessions
    m.id,
    u.id,
    reviews_data.rating,
    reviews_data.comment,
    true,
    CURRENT_TIMESTAMP - INTERVAL '1 day' * (RANDOM() * 90)::int
FROM mentors m
CROSS JOIN LATERAL (
    SELECT u.id FROM users u WHERE u.role = 'candidate' ORDER BY RANDOM() LIMIT (2 + (RANDOM() * 6)::int)
) AS random_users(user_id)
JOIN users u ON u.id = random_users.user_id
JOIN (VALUES
    (5, 'Absolutely amazing mentor! Sarah helped me understand system design concepts that I struggled with for months. Her explanations are clear and she provides real-world examples.'),
    (5, 'Outstanding session. Very knowledgeable and patient. Would definitely book again!'),
    (4, 'Great mentor with solid experience. The session was helpful but could have been more structured.'),
    (5, 'Incredible depth of knowledge and teaching ability. Sarah made complex topics easy to understand.'),
    (5, 'One of the best mentors on the platform. Highly recommend for anyone preparing for FAANG interviews.'),
    (4, 'Very helpful session. Good insights into Google''s engineering practices.'),
    (5, 'Excellent mentor! Helped me crack my system design interview. Thank you!'),
    (4, 'Solid session with practical advice. Would recommend.'),
    (5, 'Amazing experience! The session exceeded my expectations.'),
    (4, 'Good mentor with relevant experience. The session was informative.'),
    (5, 'Outstanding! This mentor really knows their stuff and explains it well.'),
    (4, 'Helpful session, learned a lot about scalable architecture.'),
    (5, 'Fantastic mentor! Very patient and encouraging.'),
    (4, 'Good session overall, would book again.'),
    (5, 'Incredible insights into the industry. Highly valuable session.'),
    (3, 'Decent session but expected more depth on some topics.'),
    (5, 'Amazing mentor! Really helped boost my confidence.'),
    (4, 'Very knowledgeable and professional. Good session.'),
    (5, 'Exceptional mentor with great teaching skills.'),
    (4, 'Solid advice and good industry insights.')
) AS reviews_data(rating, comment)
ON true
WHERE m.name IN ('Sarah Johnson', 'Mike Chen')
LIMIT 40;

-- Insert reviews for other mentors
INSERT INTO reviews (session_id, mentor_id, user_id, rating, comment, is_public, created_at)
SELECT
    NULL,
    m.id,
    (SELECT id FROM users WHERE role = 'candidate' ORDER BY RANDOM() LIMIT 1),
    4 + (RANDOM())::int, -- Random rating between 4-5
    CASE (RANDOM() * 10)::int
        WHEN 0 THEN 'Excellent mentor with deep technical knowledge!'
        WHEN 1 THEN 'Very helpful session, learned a lot!'
        WHEN 2 THEN 'Great experience, would recommend to others.'
        WHEN 3 THEN 'Knowledgeable mentor with good teaching skills.'
        WHEN 4 THEN 'Solid session with practical insights.'
        WHEN 5 THEN 'Amazing mentor! Really helped me understand complex topics.'
        WHEN 6 THEN 'Professional and experienced. Good value for money.'
        WHEN 7 THEN 'Helpful session with real-world examples.'
        WHEN 8 THEN 'Great mentor, very patient and encouraging.'
        ELSE 'Outstanding session! Highly recommend.'
    END,
    true,
    CURRENT_TIMESTAMP - INTERVAL '1 day' * (RANDOM() * 60)::int
FROM mentors m
WHERE m.name NOT IN ('Sarah Johnson', 'Mike Chen')
ORDER BY RANDOM()
LIMIT 60;

-- Display summary of added data
SELECT
    'Users' as table_name,
    COUNT(*) as total_rows
FROM users
UNION ALL
SELECT
    'Mentors' as table_name,
    COUNT(*) as total_rows
FROM mentors
UNION ALL
SELECT
    'User Preferences' as table_name,
    COUNT(*) as total_rows
FROM user_preferences
UNION ALL
SELECT
    'Skill Assessments' as table_name,
    COUNT(*) as total_rows
FROM skill_assessments
UNION ALL
SELECT
    'Reviews' as table_name,
    COUNT(*) as total_rows
FROM reviews;