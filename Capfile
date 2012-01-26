load 'deploy' if respond_to?(:namespace) # cap2 differentiator
Dir['vendor/plugins/*/recipes/*.rb'].each { |plugin| load(plugin) }


set :application, "gamemine"
set :repository,  "git@github.com:gamemine/gamemine.git"

set :scm, :git
set :use_sudo, false
set :ssh_options, { :user => "webmaster", :forward_agent => true }
set :deploy_via, :remote_cache
set :deploy_to, "/var/www/#{application}"
set :django_use_south, true


desc "Run tasks in staging enviroment."
task :staging do
  role :web, "test.gamemine.com"
  role :app, "test.gamemine.com"
  role :db,  "test.gamemine.com", :primary => true
  set :branch, "integration"
end

desc "Run tasks in personal staging enviroment."
task :t0ster do
  role :web, "t0ster.test.gamemine.com"
  role :app, "t0ster.test.gamemine.com"
  role :db,  "t0ster.test.gamemine.com", :primary => true
  set :ssh_options, { :user => "t0ster", :forward_agent => true }
  set :repository,  "git@github.com:t0ster/gamemine.git"
  set :deploy_to, "/home/t0ster/#{application}"
  set_from_env_or_ask :branch, "What branch would you like to deploy?"
end

desc "Run tasks in personal staging enviroment."
task :lelik do
  role :web, "lelik.test.gamemine.com"
  role :app, "lelik.test.gamemine.com"
  role :db,  "lelik.test.gamemine.com", :primary => true
  set :ssh_options, { :user => "lelik", :forward_agent => true }
  set :repository,  "git@github.com:gamemine/gamemine.git"
  set :deploy_to, "/home/lelik/#{application}"
  set_from_env_or_ask :branch, "What branch would you like to deploy?"
end

desc "Run tasks in personal staging enviroment."
task :nick do
  role :web, "nick.test.gamemine.com"
  role :app, "nick.test.gamemine.com"
  role :db,  "nick.test.gamemine.com", :primary => true
  set :ssh_options, { :user => "nick", :forward_agent => true }
  set :repository,  "git@github.com:gamemine/gamemine.git"
  set :deploy_to, "/home/nick/#{application}"
  set_from_env_or_ask :branch, "What branch would you like to deploy?"
end

desc "Run tasks in personal staging enviroment."
task :basil do
  role :web, "basil.test.gamemine.com"
  role :app, "basil.test.gamemine.com"
  role :db,  "basil.test.gamemine.com", :primary => true
  set :ssh_options, { :user => "basil", :forward_agent => true }
  set :repository,  "git@github.com:na/gamemine.git"
  set :deploy_to, "/home/basil/#{application}"
  set :branch, "integration"
end

desc "Run tasks in personal staging enviroment."
task :christopher do
  role :web, "christopher.test.gamemine.com"
  role :app, "christopher.test.gamemine.com"
  role :db,  "christopher.test.gamemine.com", :primary => true
  set :ssh_options, { :user => "christopher", :forward_agent => true }
  set :repository,  "git@github.com:christopher1225/gamemine.git"
  set :deploy_to, "/home/christopher/#{application}"
  set :branch, "integration"
end

desc "Run tasks in production enviroment."
task :production do
  role :web, "gamemine.com"
  role :app, "gamemine.com"
  role :db,  "gamemine.com", :primary => true
  set :branch, "master"
end


def django_manage(cmd, options={})
  path = options.delete(:path) || "#{latest_release}"
  run "cd #{path}; ./bin/django #{cmd}"
end


namespace :deploy do
  task :finalize_update, :except => { :no_release => true } do
    run "cd #{latest_release}; python bootstrap.py"
    run "cd #{latest_release}; ./bin/buildout -N"
    django_manage "collectstatic --noinput"
    run "cd #{latest_release}; ./bin/build_docs"
  end
  task :restart do
    run "sudo /usr/sbin/invoke-rc.d apache2 reload"
  end
  desc "Run manage.py syncdb in latest release."
    task :migrate, :roles => :db, :only => { :primary => true } do
      m = if fetch(:django_use_south, false) then "--migrate" else "" end
      if fetch(:django_databases, nil)
        fetch(:django_databases, nil).each { |db|
          django_manage "syncdb --noinput #{m} --database=#{db}"
        }
      else
        django_manage "syncdb --noinput #{m}"
      end
    end
end


# set_from_env_or_ask :variable, "Please enter variable name: "
# If there is VARIABLE in enviroment, set :variable to it, otherwise
# ask user for a value
def set_from_env_or_ask(sym, question)
  if ENV.has_key? sym.to_s.upcase then
    set sym, ENV[sym.to_s.upcase]
  else
    set sym do Capistrano::CLI.ui.ask question end
  end
end


namespace :django do
  desc <<EOF
Run custom Django management command in latest release.

Pass the management command and arguments in COMMAND="..." variable.
If COMMAND variable is not provided, Capistrano will ask for a command.
EOF
  task :manage do
    set_from_env_or_ask :command, "Enter management command"
    django_manage "#{command}"
  end
end
