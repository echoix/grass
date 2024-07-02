const { NR } = process.env;
return {
  "pull_request": {
    "number": NR,
    "base": { "repo": context.repo.repo },
    "head": {
      "sha": github.event.workflow_run.head_sha,
      "ref": github.event.workflow_run.head_branch
    }
  },
  "repository": {
    "name": context.repo.repo,
    "owner": { "login": context.repo.owner }
  }
}