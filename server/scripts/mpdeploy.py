"""
Call this script when you want to deploy frontend code.
"""
# TODO: Figure out why envoy fucks up commands that have messages
# like git tag and git commit

import sys
import os
import datetime
import re
import yaml
import requests
import clint
from clint.textui import puts, indent, colored
import envoy

PWD = os.path.dirname(__file__)
sys.path.append(os.path.join(PWD, '..'))


def prompt_before_executing(original, override=None):
    """
    Decorator that prompts the user before calling the function.
    Useful for debugging, you can run the whole script and pick and choose
    which individual steps you want to be run without having to comment
    stuff out. If the user selects 'n', `override` will be returned if
    it's set (some functions expect a return value).
    """
    def inner(*args, **kwargs):
        puts('Do you want to call %s with args: %s' % (original.func_name, str(args)))
        answer = raw_input("(y/n) >> ")
        if answer == 'y':
            result = original(*args, **kwargs)
            print "result was ", result
            return result
        else:
            puts('Skipped %s' % (original.func_name,))
            return override
    return inner


# Git stuff
def git(cmd, git_dir=None):
    """
    Calls a git command `cmd` from the repository in `git_dir`.
    `git_dir` is set to the mopub directory by default.
    Note that `git_dir` needs to be the path to the actual .git
    directory, not the directory that contains it.
    """
    if git_dir == None:
        git_dir = "../.."
    git_dir = os.path.join(PWD, git_dir)
    command = "git --git-dir=" + git_dir + "/.git " + cmd
    result = envoy.run(command)
    return result


#@prompt_before_executing
def git_fetch():
    return git('fetch')


#@prompt_before_executing
def git_fetch_tags():
    """
    Pulls the tag list from origin.
    """
    return git('fetch --tags')


#@prompt_before_executing
def git_push():
    current_branch_name = git_branch_name()
    return git('push origin ' + current_branch_name)


#@prompt_before_executing
def git_push_tag(tag_name):
    """
    Pushes the tag list to origin.
    """
    return git('push origin ' + tag_name)


#@prompt_before_executing
def git_list_deploy_tags():
    """
    Returns the list of deploy tags.
    This function has an informative docstring.
    """
    deploy_tags = git("tag -l deploy-*").std_out.strip().split("\n")
    return deploy_tags

def git_get_most_recent_deploy_tag():
    deploy_tags = git_list_deploy_tags()
    n = max([int(tag.replace('deploy-', '')) for tag in deploy_tags if tag.find('deploy-') >= 0])
    return 'deploy-' + str(n)


#@prompt_before_executing
def git_tag_current_deploy():
    """
    Tags the repo with a new deploy name.
    """
    # Make the tag name by finding the most recent deploy tag
    # and adding 1 to the deploy number.
    try:
        deploy_number = int(git_get_most_recent_deploy_tag().replace('deploy-',''))
        new_deploy_number = deploy_number + 1
    except IndexError, ValueError:
        new_deploy_number = 0

    new_deploy_tag = "deploy-" + str(new_deploy_number)

    # Make the message for the deploy
    deploy_datetime = datetime.datetime.now().strftime("%A, %B %d, %Y at %I:%M%p PST")
    message = "Deployed by %s on %s." % (git_get_user(), deploy_datetime)

    # Tag the commit
    #command = 'tag -m \'%s\' -a %s' % (message, new_deploy_tag)
    #result = git(command)

    # XXX: envoy fucks this up, probably because it's not
    # properly escaping something before executing. Using
    # subprocess.call instead.
    from subprocess import call
    call(["git", "tag", "-m", message, "-a", new_deploy_tag])

    return new_deploy_tag


#@prompt_before_executing
def git_commit(message):
    from subprocess import call

    if message == '':
        message = 'Deployed without finding any bug fixes.'

    call(["git", "commit", "-a", "-m", message])
    #return git('commit -a -m "%s"' % message)


#@prompt_before_executing
def git_get_user():
    """
    Gets the git username, useful for lighthouse messages.
    """
    username = git("config user.name").std_out.strip()
    return username


#@prompt_before_executing
def git_branch_name():
    """
    Gets the name of the current git branch.
    """
    result = git("branch")
    branches = [i.strip() for i in result.std_out.strip().split("\n")]

    # HACK: the current branch name has a * before its name. I assume this
    # will aways be sorted first alphabetically.
    branches.sort()

    return branches[0].lstrip("* ")


#@prompt_before_executing
def git_get_logs_for_changelog():
    """
    Gets a list of abbreviated commits since the last deploy.
    """
    most_recent_id = git_most_recent_commit_id()
    most_recent_tag = git_get_most_recent_deploy_tag()
    log = git('log --pretty=oneline --abbrev-commit ' + most_recent_tag + "..." + most_recent_id)

    return log.std_out.split('\n')


#@prompt_before_executing
def git_most_recent_commit_id():
    """
    Gets the commit id of the most recent commit. Useful in getting
    a log of commits between the most recent deploy and the current
    commit without creating a new tag.
    """
    return git('log').std_out.strip().split('\n')[0].replace("commit ", "")


#@prompt_before_executing
def git_list_resolved_tickets():
    """
    Gets a list of resolved ticket numbers by looking between
    the last two deploy tags.
    """
    # Get all of the commit log text between the last deploy (tagged deploy-<n>)
    # and the current commit. This is logs all of the commits being deployed.
    most_recent_id = git_most_recent_commit_id()
    most_recent_deploy_tag = git_get_most_recent_deploy_tag()
    log = git("log " + most_recent_deploy_tag + "..." + most_recent_id).std_out.strip().split("\n")

    # Find all of the commits that were tagged with fixes
    ticket_number_regex = re.compile("\[#(\d+) state:fixed")
    fixed_tickets = []
    for line in log:
        try:
            ticket = ticket_number_regex.search(line).group(1)
        except AttributeError:
            ticket = None
        if ticket:
            fixed_tickets += [ticket]

    return fixed_tickets


#@prompt_before_executing
def launch_deploy_process(server=None):
    """
    Launches the appengine deploy process
    """
    from subprocess import call

    if server == None:
        server = "frontend-staging"

    server_path = os.path.join(PWD, '..')

    envoy.run('cp ' + server_path + '/app.frontend.yaml ' + server_path + '/app.yaml')

    # The user will need to input a username and password for GAE
    # during the deploy process. We use subprocess.call because it
    # redirects stdout/stdin to/from the user.
    call(['appcfg.py', 'backends', server_path, 'update', server])

    # envoy.run('rm ' + server_path + '/app.yaml')


#@prompt_before_executing
def write_changelog(deploy_tag, fixed_tickets, new_commits):
    """
    Writes a markdown-parseable changelog to the CHANGELOG
    file in the mopub directory.
    """
    changelog_path = os.path.join(PWD, "../../CHANGELOG")

    # Get the contents of the current changelog
    changelog_file = open(changelog_path, 'r')
    changelog = [line.strip() for line in changelog_file.readlines()]
    changelog_file.close()

    # Make the header for the new change
    new_changelog = ["# Deployed " + datetime.datetime.utcnow().strftime("%A, %B %d, %Y at %I:%M%p PST"),
                     "### Deployed by " + git_get_user(),
                     "### Tagged " + deploy_tag,
                     "### Bugs Fixed: " + str(fixed_tickets),
                     "### Included Commits: "]

    # Add all of the recent commits
    new_changelog += [" * " + commit for commit in new_commits if commit]
    new_changelog += [" "]

    # Add the old changelog back in
    new_changelog += changelog

    # Write that shit
    changelog_file = open(changelog_path, 'w')
    changelog_file.writelines([line + '\n' for line in new_changelog])
    changelog_file.close()


def minify_javascript():

    # we use juicer for minification, alert them if they dont have it
    has_juicer = envoy.run('which juicer')
    if has_juicer.std_out == '':
        puts(colored.red('you need to install juicer to run the pre-commit hook'))
        puts(colored.red('install it with "$ gem install juicer"'))
        sys.exit(1)

    JS_DIR = os.path.join(PWD, '../public/js/')
    JS_APP_FILE = os.path.join(JS_DIR, 'app.min.js')

    envoy.run('juicer merge -s -f -o %s models/*.js views/*.js controllers/*.js utilities/*.js' % JS_APP_FILE)

    puts("Minifying Javascript files in " + JS_DIR)

    puts(colored.green('Javascript Minified'))


def update_static_version_numbers():
    versions_path = os.path.join(PWD, '../versions.yaml')
    f = open(versions_path,'r')
    config = yaml.load(f)
    f.close()
    # REFACTOR: check to see if files have been updated first
    config['scripts'] += 1
    config['styles'] += 1

    f = open(versions_path,'w')
    yaml.dump(config, f)
    f.close()


def post_to_hipchat(message, room_id, files={}):
    url = "https://api.hipchat.com/v1/rooms/message?" + \
          "format=json" + \
          "&auth_token=3ec795e1dd7781d59fb5b8731adef1" + \
          "&room_id=" + room_id + \
          "&from=Alerts" + \
          "&message=" + str(message).replace(' ', '%20')


    response = requests.post(url)
    return response



def main():
    """
    Start the

           /$$                     /$$                     /$$
          | $$                    | $$                    | $$
      /$$$$$$$  /$$$$$$   /$$$$$$ | $$  /$$$$$$  /$$   /$$| $$
     /$$__  $$ /$$__  $$ /$$__  $$| $$ /$$__  $$| $$  | $$| $$
    | $$  | $$| $$$$$$$$| $$  \ $$| $$| $$  \ $$| $$  | $$|__/
    | $$  | $$| $$_____/| $$  | $$| $$| $$  | $$| $$  | $$
    |  $$$$$$$|  $$$$$$$| $$$$$$$/| $$|  $$$$$$/|  $$$$$$$ /$$
     \_______/ \_______/| $$____/ |__/ \______/  \____  $$|__/
                        | $$                     /$$  | $$
                        | $$                    |  $$$$$$/
                        |__/                     \______/
    """
    puts(colored.blue("Starting deploy"))

    with indent(2, quote=colored.blue('+')):
        try:

            # Setup. Get the branch name and deploy server and verify that's
            # what the user wanted.
            active_branch_name = git_branch_name()
            deploy_server = clint.args.get(0)
            deployer = git_get_user()

            if active_branch_name != "master":
                puts(colored.yellow("Careful! You're deploying a non-master branch."))
                y_or_n = raw_input('Are you sure you want to deploy ' + active_branch_name + '? (y/n) >> ')
                if y_or_n == 'n':
                    sys.exit(1)

            if deploy_server == 'frontend-0':
                # Update the repo with tags that might have been made from other deploys
                puts("Updating the tag list from origin")
                git_fetch()
                git_fetch_tags()

                # Get a list of tickets that were fixed.
                puts("Getting a list of the tickets that were fixed in this deploy")
                fixed_tickets = git_list_resolved_tickets()
                if len(fixed_tickets) == 0:
                    puts(colored.yellow("Didn't find any ticket fixes"))
                else:
                    puts("Found " + str(len(fixed_tickets)) + \
                         " bug fixes in this deploy: " + colored.green(str(fixed_tickets)))

                # Get the commits that will go into the changelog
                new_commits = git_get_logs_for_changelog()

                # Tag the commit with the deploy number
                deploy_tag_name = git_tag_current_deploy()
                puts("Tagged this deploy's commits as " + colored.green(deploy_tag_name))

                # Push all tags
                puts("Updating origin with the new tag")
                git_push_tag(deploy_tag_name)

                # Minify all javascript
                puts("Minifying Javascript")
                minify_javascript()

                # Updating version numbers
                puts("Updating Version Numbers")
                update_static_version_numbers()

                # Write to the changelog
                puts("Writing changelog")
                write_changelog(deploy_tag_name, fixed_tickets, new_commits)

                # Update the repository with the new changelog
                # Lighthouse will notice this and will update everyone with the new
                puts("Updating origin with the changelog")
                commit_message = " ".join(['[#%s state:resolved]' % str(ticket) for ticket in fixed_tickets])
                git_commit(commit_message)
                git_push()

                # notify people of a successful deploy on hipichat
                post_to_hipchat("Branch %s just deployed to %s by %s" % (active_branch_name,
                                                                         deploy_server,
                                                                         deployer))

            else:
                puts("Skipping ticket update process because you're not deploying to production")

            # Deploy the branch to the server
            if deploy_server == None:
                puts(colored.yellow('No deploy server specified, deploying to frontend-staging'))
                deploy_server = 'frontend-staging'

            puts("Deploying " + colored.green(active_branch_name) + " to " + colored.green(deploy_server))
            launch_deploy_process(server=deploy_server)

        except Exception, error:
            puts(colored.red("Deploy failed."))
            puts(colored.red(str(error)))


if __name__ == "__main__":
    main()
