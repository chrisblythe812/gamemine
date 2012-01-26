from fabric.api import * #@UnusedWildImport


env.hosts = ['webmaster@gamemine.com']

def deploy():
    local('git push')
    with cd('~/gamemine'):
        run('git pull')
        run('sudo /usr/sbin/invoke-rc.d apache2 restart')


def deploy_with_db():
    local('git push')
    with cd('~/gamemine'):
        run('git pull')
        run('./manage migrate')
        run('sudo /usr/sbin/invoke-rc.d apache2 restart')

def update():
    local('git push')
    with cd('~/gamemine'):
        run('git pull')
    
