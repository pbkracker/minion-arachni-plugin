#!/usr/bin/env ruby

require 'arachni/rpc/pure'
require 'cgi'
require 'pp'

# You must have arachni_rpcd running for this to work.
# This currently relies on the experimental branch of arachni.
# https://github.com/Arachni/arachni/tree/experimental#source

url_to_scan = 'http://testfire.net'
if ARGV.size > 0
        url_to_scan = ARGV[0]
end
puts "Arachni will scan this URL: " + url_to_scan


# TODO: Read cookies from a file or from the argument list.
static_cookies = [
    {
           "Cookie1"=>"true",
    },
    {
           # Arachni automatically escapes values.  If your values are already escaped, you
           # may want to un-escape them before sending them to arachni.
           "Cookie2"=>CGI::unescape("v%3D2"),
    }
]

dispatcher = Arachni::RPC::Pure::Client.new(
    host: 'localhost',
    port:  7331
)

instance_info = dispatcher.call( 'dispatcher.dispatch' )

host, port = instance_info['url'].split( ':' )
instance = Arachni::RPC::Pure::Client.new(
    host:  host,
    port:  port,
    token: instance_info['token']
)

# Avoid having to keep writing instance.call( 'service.<method>', ... )
service = Arachni::RPC::RemoteObjectMapper.new( instance, 'service' )

#puts static_cookies

service.scan url: url_to_scan,
             audit_links: true,
             audit_forms: true,
             link_count_limit: 5,
             cookies: static_cookies,
             audit_cookies: true,
             audit_headers: true,
             exclude: ['SignOut'],
             debug: false,
             # load all XSS modules
             modules: 'xss*'
             # Just audit the first page.
             #proxy_host: '10.2.178.166',
             #proxy_port: '8080',
             #follow_subdomains: true


while sleep 1
    progress = service.progress( with: :issues )

    puts "Percent Done:   [#{progress['stats']['progress']}%]"
    puts "Current Status: [#{progress['status'].capitalize}]"

    if progress['issues'].any?
        puts
        puts 'Issues thus far:'
        progress['issues'].each do |issue|
            puts "  * #{issue['name']} on '#{issue['url']}'."
        end
    end

    puts '-' * 50

    # we're done
    break if !progress['busy']
end

puts "-----[REPORT FOLLOWS]-----"

# Grab the report as a Hash.
pp service.report

# Kill the instance and its process, no zombies please...
service.shutdown


