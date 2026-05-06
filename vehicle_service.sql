create database vehicle_service;
use vehicle_service;
CREATE TABLE services(
    customer_name VARCHAR(100),
    vehicle_number VARCHAR(50),  
    service_type VARCHAR(100),
    service_date DATE
);
DELETE FROM services;


select * from services;
DELETE FROM services
WHERE customer_name=rrr;