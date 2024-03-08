create table if not exists residents (
	id int auto_increment primary key,
    name varchar(255),
    date_of_birth date,
    level_of_care varchar(100)
);

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