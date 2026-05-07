create or replace view vw_upcoming_expirations as
select cr.record_id, cr.collaborator_id, cr.certification_id, cr.expiration_date, cr.status
from certification_record cr
where cr.expiration_date between current_date and current_date + interval '90 days';

create or replace view vw_assignment_backlog as
select assignment_id, assignee_id, certification_id, due_date, priority, status
from certification_assignment
where status in ('ASSIGNED','IN_PROGRESS','SUBMITTED');
