
[[_TOC_]]

# Change Request Process

Feature updates, bug fixes, etc should follow the process below

1. [Create an issue](https://gitlab.rosetta.ericssondevops.com/sa-bss-charging-cns/cec-adaptation-pod/-/issues/new)
2. From the issue, create a Merge Request (MR). This will also create a branch. Note your branch name
3. In VS Code, fetch all branches (Ctrl+Shift+P, `Git: Fetch From All Remotes`), switch to your branch.
4. Work on your code in your branch. Attach testing evidence to the GitLab issue (logs etc)
5. Commit changes to your branch in VS Code and push to the GitLab server
6. In GitLab, mark the Merge Request (MR) as "ready for review". This starts a code review
  - Lab testing performed successfully, with the committed code updates
  - Review of code, to ensure safety, readability and maintainability
  - CR created for deployment

7. Once your code is reviewed and merged (upon MR approval), CICD pipeline is triggered, which will automatically build the package and  deliver it to production environment. Last stage of the pipelie is a manual button, which should be pressed during maintenacne window to deploy the code to production cluster.

# Set up the environment

## Tools

Install the following tools:

- [VS Code](https://code.visualstudio.com/)
- [Git Bash](https://git-scm.com/downloads)
- [cloudflared](https://docs.pages.rosetta.ericssondevops.com/kb/support/rosetta-support/windows-access-config/)

to install cloudflared (in Git Bash):

- `mkdir /c/cloudflared && curl -L -o /c/cloudflared/cloudflared.exe https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe`
- add `C:\cloudflared` to PATH


to install cloudflared (Ubuntu 22.04 LTS):

```
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared jammy main' | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt-get update && sudo apt-get install cloudflared
```

`vi ~/.ssh/config`

paste and save:

```
Host git.rosetta.ericssondevops.com 
         ProxyCommand cloudflared access ssh --hostname %h
```
## Configure Git and SSH keys

in Git Bash

Set your username: `git config --global user.name "firstName lastName"`

Set your email address: `git config --global user.email "yourname@ericsson.com"`

Generate ssh key (if you already have ssh keys in `~/.ssh` you can skip this step)

`ssh-keygen`

Copy the public key to clipboard

`cat ~/.ssh/id_rsa.pub | clip`

Add it to your account in GitLab

1. Open https://gitlab.rosetta.ericssondevops.com/-/profile/keys
2. Paste the key from clipboard to **Key** Text Box
3. Click **Add Key** button

## Clone the repository

We recommend to put all git projects in the same folder (in this case, `~/workspace`)

In Git Bash

```bash
mkdir ~/workspace && cd ~/workspace
git clone git@git.rosetta.ericssondevops.com:sa-bss-charging-cns/cec-adaptation-pod.git
```
