# Users and invitations

Use this reference for the authenticated `Usuários` page.

## Read users and invitations

The users table contains username, email, status, and creation date. `Convites
anteriores` lists active invitations with email and expiration.

The platform has only active/inactive status. It has no roles, granular
permissions, teams, or user deletion.

## Invite a new user

Use `Gerar convite`, enter the exact recipient email, preview it, confirm, then
use `Gerar e copiar link`. The recipient must open the public link and choose
their own username and password.

An invitation expires after 72 hours and can be used once. Creating another
invitation for the same email replaces the previous active invitation. Include
that impact in the preview when relevant. The interface has no explicit revoke
action.

Treat the invitation link as sensitive. Do not paste it into chat or claim it was
emailed; the platform only copies the link.

## Edit a user safely

Use the row action `Editar {username}`. Username, email, and active/inactive status
may be changed after a confirmed preview. Leave `Nova senha` empty.

Never create a user through `Novo usuário` because that dialog requires choosing
their password. Never change a password, ask for it, expose it, or type it. The
current user cannot deactivate their own account.
