# portfolioOS Agent Skills

Upload this archive as one custom skill in Claude or ChatGPT. The root skill
routes natural-language requests to the published workflows bundled in its
`skills/` folder.

## Claude

Open the custom-skills area, upload `portfolioos.zip`, and enable the package.

## ChatGPT

Open the Skills area, create a skill by uploading `portfolioos.zip`, and enable
the package.

Availability depends on the user's plan and the workspace policies configured by
an administrator.

The archive also carries `.codex-plugin` and `.claude-plugin` manifests for
runtimes that install the same folder as a plugin. Those runtimes discover each
workflow directly under `skills/`.

## Updates and safety

Upload a new archive to update the complete package. Review the included
instructions before use, never provide credentials in chat, and confirm every
write operation before the agent submits it.
