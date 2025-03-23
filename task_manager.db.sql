BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "groups" (
	"group_id"	INTEGER,
	"group_name"	TEXT,
	"created_by"	TEXT,
	"color"	TEXT,
	"remarks"	TEXT,
	"isTemplate"	INTEGER DEFAULT 0,
	PRIMARY KEY("group_id" AUTOINCREMENT),
	FOREIGN KEY("created_by") REFERENCES "users"("username")
);
CREATE TABLE IF NOT EXISTS "task_link" (
	"id"	INTEGER UNIQUE,
	"task_id"	INTEGER,
	"pre_task_id"	INTEGER,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "tasks" (
	"task_id"	INTEGER,
	"task_name"	TEXT,
	"notification_days"	INTEGER,
	"due_date"	INTEGER,
	"completed"	INTEGER DEFAULT 0,
	"notified"	INTEGER DEFAULT 0,
	"group_id"	INTEGER,
	"created_by"	TEXT,
	"remarks"	TEXT,
	PRIMARY KEY("task_id" AUTOINCREMENT),
	FOREIGN KEY("created_by") REFERENCES "users"("username"),
	FOREIGN KEY("group_id") REFERENCES "groups"("group_id")
);
CREATE TABLE IF NOT EXISTS "templates" (
	"template_id"	INTEGER,
	"template_name"	TEXT,
	"created_by"	TEXT,
	PRIMARY KEY("template_id" AUTOINCREMENT),
	FOREIGN KEY("created_by") REFERENCES "users"("username")
);
CREATE TABLE IF NOT EXISTS "users" (
	"username"	TEXT,
	"password"	TEXT,
	"full_name"	TEXT,
	"address"	TEXT,
	"gender"	TEXT,
	"contact"	TEXT,
	"timezone"	TEXT,
	"email"	TEXT,
	"view_preference"	TEXT DEFAULT 'calendar',
	PRIMARY KEY("username")
);
INSERT INTO "groups" VALUES (1,'Development','admin',NULL,NULL,0);
INSERT INTO "groups" VALUES (2,'TEST2','admin',NULL,NULL,0);
INSERT INTO "groups" VALUES (3,'test3','admin','#ff0000',NULL,0);
INSERT INTO "groups" VALUES (18,'Farming','admin','#1e6200','Sample Group Template',0);
INSERT INTO "groups" VALUES (19,'School','admin','#050062','Sample Group Template',0);
INSERT INTO "groups" VALUES (20,'Template TEST','admin','#ff0000','ddd',1);
INSERT INTO "groups" VALUES (21,'Generic Farming','admin','#0a4101','Generic Farming',1);
INSERT INTO "groups" VALUES (22,'Farming Test User','test','#44ad56','tesr',0);
INSERT INTO "groups" VALUES (23,'tett','admin','#8E44AD','yeedy',0);
INSERT INTO "task_link" VALUES (1,15,12);
INSERT INTO "task_link" VALUES (2,15,11);
INSERT INTO "task_link" VALUES (3,17,16);
INSERT INTO "task_link" VALUES (4,18,16);
INSERT INTO "task_link" VALUES (5,18,17);
INSERT INTO "tasks" VALUES (1,'Reminder: Buy textbooks for next year',60,'2025-11-02',1,1,NULL,NULL,NULL);
INSERT INTO "tasks" VALUES (2,'Task: Buy textbooks',30,'2025-12-02',0,1,NULL,NULL,NULL);
INSERT INTO "tasks" VALUES (3,'Reminder: Buy reminder',14,'2025-12-18',0,0,NULL,NULL,NULL);
INSERT INTO "tasks" VALUES (4,'D-Day: Buy textbooks',0,'2026-01-01',0,0,NULL,NULL,NULL);
INSERT INTO "tasks" VALUES (5,'Reminder: Enroll for your course (30 days before)',30,'2025-12-02',0,1,NULL,NULL,NULL);
INSERT INTO "tasks" VALUES (6,'Reminder: Enroll for your course (14 days before)',14,'2025-12-18',0,0,NULL,NULL,NULL);
INSERT INTO "tasks" VALUES (7,'Reminder: Enroll for your course (7 days before)',7,'2025-12-25',0,0,NULL,NULL,NULL);
INSERT INTO "tasks" VALUES (8,'On Enrollment Day: Enroll for your course',0,'2026-01-01',0,0,NULL,NULL,NULL);
INSERT INTO "tasks" VALUES (9,'Reminder: Email if you want to change course or withdraw (14 days before)',14,'2025-12-18',0,0,NULL,NULL,NULL);
INSERT INTO "tasks" VALUES (10,'Reminder: Email if you want to change course or withdraw (7 days before)',7,'2025-12-25',0,0,NULL,NULL,NULL);
INSERT INTO "tasks" VALUES (11,'Purchase Seeds',3,'2025-03-06',1,0,18,'admin','Buy seed from walmart!');
INSERT INTO "tasks" VALUES (12,'Plant seed',3,'2025-03-09',1,0,18,'admin','Plant the purchase seed ');
INSERT INTO "tasks" VALUES (15,'Harvest',1,'2025-03-13',0,1,18,'admin',NULL);
INSERT INTO "tasks" VALUES (16,'Plant Seeds',3,'2025-03-16',0,1,21,'admin',NULL);
INSERT INTO "tasks" VALUES (17,'Fertilize seed',1,'2025-03-23',0,1,21,'admin',NULL);
INSERT INTO "tasks" VALUES (18,'Harvest',1,'2025-03-30',0,0,21,'admin',NULL);
INSERT INTO "tasks" VALUES (19,'Plant Seeds',3,'2025-03-12',1,1,22,'test',NULL);
INSERT INTO "tasks" VALUES (20,'Fertilize seed',1,'2025-03-19',0,1,22,'test',NULL);
INSERT INTO "tasks" VALUES (21,'Harvest',1,'2025-03-26',0,1,22,'test',NULL);
INSERT INTO "tasks" VALUES (22,'Plant Seeds',3,'2025-03-19',0,1,23,'admin',NULL);
INSERT INTO "tasks" VALUES (23,'Fertilize seed',1,'2025-03-26',0,1,23,'admin',NULL);
INSERT INTO "tasks" VALUES (24,'Harvest',1,'2025-04-02',0,0,23,'admin',NULL);
INSERT INTO "templates" VALUES (1,'Primary/Secondary School','admin');
INSERT INTO "templates" VALUES (2,'Enrollment for Uni','admin');
INSERT INTO "users" VALUES ('limjj11','Abcd121!','JJ','140123','Male','88828856',NULL,NULL,'calendar');
INSERT INTO "users" VALUES ('admin','admin','','','Male','',NULL,NULL,'list');
INSERT INTO "users" VALUES ('test','test','TestUser','TestUser','Male','TestUser',NULL,NULL,'calendar');
INSERT INTO "users" VALUES ('Guhendran','G3u0g1u0!','Guhendran','-','Male','91088505',NULL,'guhendranbenny@gmail.com','calendar');
COMMIT;
