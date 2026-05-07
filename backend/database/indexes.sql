create index ix_collaborator_email on collaborator(email);
create index ix_record_collaborator_status on certification_record(collaborator_id,status);
create index ix_record_expiration on certification_record(expiration_date);
create index ix_assignment_assignee_status_due on certification_assignment(assignee_id,status,due_date);
create index ix_audit_entity on audit_log(entity_type,entity_id,occurred_at desc);
create index ix_ai_tool_conversation on ai_tool_invocation(conversation_id,created_at desc);
