-- Create database (run once, as admin if needed)
-- CREATE DATABASE marathi_english;
-- GO
-- USE marathi_english;
-- GO

-- Table for Marathi–English translation pairs (used by excel_to_mssql.py)
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_NAME = N'marathi_english_pairs'
)
CREATE TABLE marathi_english_pairs (
    id INT IDENTITY(1,1) PRIMARY KEY,
    marathi_text NVARCHAR(MAX) NOT NULL,
    english_text NVARCHAR(MAX) NOT NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE()
);
GO
