select * from certification_record where expiration_date is not null and expiration_date < issue_date;
select certification_id, credential_id, count(*) from certification_record where credential_id is not null group by certification_id, credential_id having count(*) > 1;
select * from certification_record where expiration_date < current_date and status not in ('EXPIRED','RENEWED','REVOKED');
select ca.* from certification_assignment ca join collaborator c on c.collaborator_id=ca.assignee_id where c.employment_status <> 'ACTIVE';
