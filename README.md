DB

group(group_id,group_name,created_by,color,remarks)

- to add isTemplate, so if its template can use to duplicate

tasks(task_id,template_id,task_name,notification_days,due_date,completed,notified,group_id,created_by)

- to remove template_id, use group_id to link back to group

templates

- To remove as application should use group and check if istemplate

users(username,password,full_name,adress,gender,contact,timezone,email,view_preference)

-