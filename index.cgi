#!/usr/bin/perl
######################################################################################
#
# blurt 1.0 : a minimalist blogging tool by matthijs de jonge (matthijs@rommelhok.com)
#
# you'll want to change some settings below where it says "change these settings"
# (this use stuff you shouldn't touch 
######################################################################################

use Data::Dumper;
use strict;
use global;


##################################################################################
#
# change these settings
#
##################################################################################
# how many posts do you want to show on one page?
my $NumPosts = 1;
# where is the main index.cgi stored on the server?
our $BaseDir = "/path/to/blurt";
# what's the url of our site?
our $BasePath = "http://url";


# uncomment (ie remove the #) the line below if your url isn't in the server root
#our $BlogPath = $BasePath."/index.cgi";
# comment out (ie add a # to the beginning) the line below if your url isn't in the 
# server root
our $BlogPath = $BasePath;

# if you're developing blurt, you'll want to set this to a higher 
# value to get debug output
my $LogLevel = -2;

# you probably don't want to touch these unless you insist on storing your templates
# plugins and posts somewhere else
our $TemplatesDir = "$BaseDir/templates";
our $PluginsDir = "$BaseDir/plugins";
our $PostsDir = "$BaseDir/posts";
our $DefaultFlavor = 'html';
our $DefaultHeader = "Content-type: text/html\n\n";


##################################################################################
#
# everything below this line is the script itself. don't touch it unless
# you know what you're doing

our $Output = '';

our $PrevLink = '';
our $NextLink = '';
our $PageNum = 0;

our $QueryVars = &GetQueryVars();

#############################################
#
# Load requested stories
#
# TODO: this is hideous code. clean it up
our $RequestURI = $ENV{'REQUEST_URI'};
$RequestURI =~ s/^\///;
# strip off everything up to and including index.cgi because we don't care
$RequestURI =~ s/^.+\/index.cgi\/*//;
&WriteLog($LogLevel, 3, "Requesting URI $RequestURI");
our $Flavor = $DefaultFlavor;
# special case: the URI ends with index.flavor
# in that case, change the flavor and strip the index bit
if($RequestURI =~ s/\/*(index\.(\w+))$//) {
    &WriteLog($LogLevel, 2, "We're requesting a different flavor: $2");
    $Flavor = $2;
};
our @Posts;
unless($RequestURI =~ /\.\w+$/) {
# See if we want a given page number
    if($RequestURI =~ s/\/*Page(\d+)$//) {
        $PageNum = $1;
        &WriteLog($LogLevel, 3, "Requesting page number $PageNum");
    };
    my $RequestYear = '';
    my $RequestMonth = '';
    my $RequestDay;
    my $RequestDate ='';


    if($RequestURI =~ s/\/*((\d+\/*)+)$//) {
        &WriteLog($LogLevel, 3, "Found a request date: $1");
        $RequestDate = "/$1";
        ($RequestYear, $RequestMonth, $RequestDay) = split(/\//, $1);
    };
    &WriteLog($LogLevel, 3, "After processing, requesting URI is $RequestURI request date $RequestYear/$RequestMonth/$RequestDay ");
    my $PostsPath = $PostsDir."/$RequestURI";
    my @AllPosts = &GetPosts($PostsPath, $RequestYear, $RequestMonth, $RequestDay);
    &WriteLog($LogLevel, 3, "Found posts: ".Dumper(\@AllPosts));
    &WriteLog($LogLevel, 3, "Limiting to the first $NumPosts posts");

# individual entries are treated differently
    for(my $i = ($PageNum * $NumPosts); $i < (($PageNum + 1) * $NumPosts);$i++) {
        if($AllPosts[$i]) {
            push(@Posts, $AllPosts[$i]);
        };
    };

    my $PageNumPrev = $PageNum + 1;
    my $PageNumNext = $PageNum - 1;

    if(($PageNumPrev *$NumPosts) < scalar @AllPosts) {
        $PrevLink = "$BlogPath/$RequestURI/$RequestDate/Page$PageNumPrev";
        # TODO: ugly hack to get double slashes out
        $PrevLink =~ s/\/\/*/\//g;
        $PrevLink =~ s/^http:\//http:\/\//;
    };
    if($PageNumNext > -1) {
        $NextLink = "$BlogPath/$RequestURI/$RequestDate/Page$PageNumNext";
        $NextLink =~ s/\/\/*/\//g;
        $NextLink =~ s/^http:\//http:\/\//;
    };
} else {
    # this is for individual entries
    $RequestURI =~ s/\.(\w+?)$/.txt/;
    $Flavor = $1;
    $RequestURI =~ /^\/*(\w+?)\//;
    my $PostCategoryPath = "$PostsDir/$1";
    my $PostPath = "$PostsDir/$RequestURI";
    &WriteLog($LogLevel, 2, "Path for post $RequestURI is $PostCategoryPath");
    $Posts[0] = $PostPath;
    # build next / prev links
    my $PrevPostPath = '';
    my $NextPostPath = '';
    my @PeerPosts = &GetPosts($PostCategoryPath);
    &WriteLog($LogLevel, 2, "Peer posts are ".Dumper(\@PeerPosts));
    my $PostNum = 0;
    for(my $i = 0; $i < scalar @PeerPosts; $i++) {
        if(@PeerPosts[$i] eq $PostPath) {
            $PostNum = $i;
        };
    };
    &WriteLog($LogLevel, 3, "Post is number $PostNum");
    unless($PostNum == (scalar @PeerPosts - 1)) {
        $PrevPostPath = $PeerPosts[$PostNum + 1];
        $PrevPostPath =~ s/^$PostsDir//;
        $PrevPostPath =~ s/\.txt$/.$Flavor/i;
        $PrevLink = $BlogPath.$PrevPostPath;
    };
    if($PostNum) {
        $NextPostPath = $PeerPosts[$PostNum - 1];
        $NextPostPath =~ s/^$PostsDir//;
        $NextPostPath =~ s/\.txt$/.$Flavor/i;
        $NextLink = $BlogPath.$NextPostPath;
    };
    &WriteLog($LogLevel, 3, "Prev post is $PrevPostPath next post is $NextPostPath");
};
&WriteLog($LogLevel, 2, "Showing posts: ".Dumper(\@Posts));



##########################
#
# plugins get loaded here
#
#
opendir(PLUGINS, $PluginsDir);
my @Plugins = sort(grep(/\.pm$/i ,grep(!/^\./, readdir(PLUGINS))));
&WriteLog($LogLevel, 3, "Plugins dir contains ".Dumper(\@Plugins));
closedir(PLUGINS);
foreach my $Plugin (@Plugins) {
    my $PluginPath = $PluginsDir."/$Plugin";
    &WriteLog($LogLevel, 2, "Executing plugin $PluginPath");
    do $PluginPath;
    $Plugin =~ s/\.pm$//;
};

##########################
#
# Assemble output
#
#
my $HeadFile = "$TemplatesDir/head.$Flavor";
my $FootFile = "$TemplatesDir/foot.$Flavor";
my $StoryFile = "$TemplatesDir/story.$Flavor";

$Output .= &ProcessTemplate($HeadFile);

our $Title;
our $PostContent;
our $PostYear;
our $PostMonth;
our $PostDay;
our $PostPath;
our $PostID;

foreach my $PostFile (@Posts) {
    open(POST, "<:utf8", $PostFile);
    while(<POST>) {
        unless($Title) {
            $Title = $_;
        } else {
            $PostContent .= $_;
        };
    };
    close POST;
    ($PostYear, $PostMonth, $PostDay) = &GetPostDate($PostFile);
    foreach my $Plugin (@Plugins) {
        &WriteLog($LogLevel, 3,"Letting plugin $Plugin process post $PostFile");
        $Plugin->ProcessPost($PostFile);
    };
    $PostFile =~ /\/([\w\s\-_]+?)\/([\w\s\-_]+?)\.txt$/;
    $PostPath = $1;
    $PostID =  $2;
    $Output .= &ProcessTemplate($StoryFile);
    $Title = '';
    $PostContent = '';
    $PostID = '';
    $PostPath = '';
    $PostYear = '';
    $PostMonth = '';
    $PostDay = '';

};

$Output .= &ProcessTemplate($FootFile);

print $DefaultHeader;
print $Output;


sub ProcessTemplate {
    my $TemplateFile = shift;
    my $Output = '';
    open(TEMPLATE, "<:utf8", $TemplateFile) || &WriteLog($LogLevel, 1, "Unable to open $TemplateFile for reading:$!\n");
    while(<TEMPLATE>) {
        $Output .= $_;
    };
    no strict "refs";
    $Output =~ s/(\$\w+(?:::)?\w*)/"defined $1 ? $1 : ''"/gee;
    use strict "refs";
    close TEMPLATE;
    return $Output;
};

sub GetQueryVars() {
    # GET queries get appended to the request URI. we don't want
    # them there.
    $ENV{'REQUEST_URI'} =~ s/\?.+$//;
    my $QueryVars = {};
    my @Vars;
    if($ENV{'REQUEST_METHOD'} eq 'GET') {
        my $QueryString = $ENV{'QUERY_STRING'};
        @Vars = split(/\&/, $QueryString);
    } else {
        my $RequestBuffer = '';
        read (STDIN, $RequestBuffer, $ENV{'CONTENT_LENGTH'});
        &WriteLog($LogLevel, 2, "Request buffer is $RequestBuffer");
        @Vars = split(/\&/, $RequestBuffer);
    };
    foreach my $Var (@Vars) {
        (my $Key, my $Value) = split(/\=/, $Var);
        # Late HTTP decoding to make sure we're not getting
        # confused by people entering & in form inputs
        $Key = &DecodeHTTP($Key);
        $Value = &DecodeHTTP($Value);
        $QueryVars->{$Key} = $Value;
    };
    &WriteLog($LogLevel, 2, Dumper($QueryVars));
    return $QueryVars;
};

# undo the nasty effects of http encoding
sub DecodeHTTP {
    my $Input = shift;
    $Input =~ tr/+/ /;
    $Input =~ s/%(..)/pack("C", hex($1))/eg;

    return $Input;
};
                
