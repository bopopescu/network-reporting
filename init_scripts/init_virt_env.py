import subprocess
import sys
import os


def main():
    if len(sys.argv) != 2:
        print 'Usage: python create_virt_env.py VIRT_ENV_LOC'
        print 'Example: python create_virt_env mk_virtual_env'
        return
    virt_home_dir = sys.argv[1]
    DIR_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    print call_command('sudo easy_install pip')
    print call_command('sudo pip install virtualenv')
    if not os.path.exists(virt_home_dir):
        print call_command('virtualenv --no-site-packages --distribute %s -p python2.5' % virt_home_dir)
    print call_command('pip install -E %s -r requirements.txt' % virt_home_dir)
    
    # symbolic link the
    REPO_DIR_PATH = os.path.join(os.path.split(DIR_PATH)[0], '.pylintrc')
    print call_command('ln -s %s %s' % (REPO_DIR_PATH,
                                        os.path.join(virt_home_dir, 'bin', '.pylintrc')
                                       )
                       )

def call_command(command):
    process = subprocess.Popen(command.split(' '),
                               stderr=subprocess.PIPE)
    return process.communicate()

if __name__ == "__main__":
    main()
