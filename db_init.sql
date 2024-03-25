create table if not exists users (
	user_id int auto_increment primary key,
    username varchar(150) unique not null,
    password_hash varchar(255) not null,
    user_role varchar(100) not null,
    initials varchar(30),
    is_temp_password tinyint(1) default 1
);

create table if not exists user_settings (
	id int auto_increment primary key,
    setting_name varchar(100) unique,
    setting_value varchar(150)
);

create table if not exists documents (
	document_id int auto_increment primary key,
    document_name varchar(255) not null,
    expiration_interval int, -- In days; NULL or 0 for documents without a fixed interval
    is_custom boolean default false,
    category enum('Employee', 'Resident', 'Facility') default 'Facility'
);

create table if not exists tracked_items (
	item_id int auto_increment primary key,
    document_id int,
    document_date date not null,
    expiration_date date not null,
    reminder_days_before_expiration int default 30,
    document_status enum('valid', 'Expiring Soon', 'Expired') not null,
    pertains_to varchar(255) default null,
    foreign key (document_id) references documents(document_id)
);

create table if not exists activities (
	id int auto_increment primary key,
    activity_name varchar(255) not null
);

create table if not exists meals (
	id int auto_increment primary key,
    meal_type varchar(50) not null,
    meal_option text not null,
    default_drink varchar(100) default null
);

create table if not exists residents (
	id int auto_increment primary key,
    name varchar(255),
    date_of_birth date,
    level_of_care varchar(100)
);

create table if not exists adl_chart (
 	chart_id int auto_increment primary key,
     resident_id int,
     chart_date date,
     first_shift_sp varchar(100),
     second_shift_sp varchar(100),
     first_shift_activity1 varchar(100),
     first_shift_activity2 varchar(100),
     first_shift_activity3 varchar(100),
     second_shift_activity4 varchar(100),
     first_shift_bm varchar(100),
     second_shift_bm varchar(100),
     shower varchar(100),
     shampoo varchar(100),
     sponge_bath varchar(100),
     peri_care_am varchar(100),
     peri_care_pm varchar(100),
     oral_care_am varchar(100),
     oral_care_pm varchar(100),
     nail_care varchar(100),
     skin_care varchar(100),
     shave varchar(100),
     breakfast tinyint,
     lunch tinyint,
     dinner tinyint,
     snack_am tinyint,
     snack_pm tinyint,
     water_intake tinyint,
     foreign key (resident_id) references residents(id),
     unique (resident_id, chart_date)
 ) engine=InnoDB;

create table if not exists audit_logs (
	log_id int auto_increment primary key,
    username varchar(255),
    activity varchar(255),
    details text,
    log_time datetime
);

create table if not exists time_slots (
	id int auto_increment primary key,
    slot_name varchar(100) unique
);

insert into time_slots (slot_name) values ('Morning'), ('Noon'), ('Evening'), ('Night')
on duplicate key update slot_name = values(slot_name);

create table if not exists medications (
	id int auto_increment primary key,
    resident_id int,
    medication_name varchar(200),
    dosage varchar(175),
    instructions text,
    medication_type varchar(50) default 'Scheduled',
    medication_form varchar(50) default 'Pill',
    count int default null,
    discontinued_date date default null,
    foreign key (resident_id) references residents(id)
)engine= InnoDB;

create table if not exists medication_time_slots (
	medication_id int,
    time_slot_id int,
    foreign key (medication_id) references medications(id),
    foreign key (time_slot_id) references time_slots(id),
    primary key (medication_id, time_slot_id)
);

create table if not exists emar_chart (
	chart_id int auto_increment primary key,
    resident_id int,
    medication_id int,
    chart_date date,
    time_slot varchar(100),
    administered varchar(100),
    current_count int default null,
    notes text,
    foreign key(resident_id) references residents(id),
    foreign key(medication_id) references medications(id),
    unique(resident_id, medication_id, chart_date, time_slot) 
) engine=InnoDB;

create table if not exists non_medication_orders (
	order_id int auto_increment primary key,
    resident_id int,
    order_name varchar(255) not null,
    frequency int,
    specific_days text,
    special_instructions text,
    discontinued_date date default null,
    last_administered_date date default null,
    foreign key (resident_id) references residents(id)
) engine=InnoDB;