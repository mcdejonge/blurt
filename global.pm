#################################################
#
#
# some blurt global functions that should be merged
# into the main index.cgi at some point in time
package global;
use strict;

my $LogLevel = -1;
use Data::Dumper;
require Exporter;

our @ISA = qw(Exporter);

our @EXPORT = qw(WriteLog GetPosts GetPostDate);

sub GetPostDate {
    my $PostFullPath = shift;
    my $PostDateStamp = (stat($PostFullPath))[9];
    &WriteLog($LogLevel, 3, "Date stamp for $PostFullPath is $PostDateStamp");
    (undef, undef, undef, my $Day, my $Month, my $Year, undef) = localtime($PostDateStamp);
    $Day = &PadWithChar($Day, 2, '0');
    $Month = &PadWithChar($Month + 1 , 2, '0');
    $Year = $Year + 1900;
    &WriteLog($LogLevel, 3, "For $PostFullPath time stamp is $PostDateStamp which is year $Year month $Month day $Day");
    return ($Year, $Month, $Day);
};
sub GetPosts{
  my $PostsDir = shift;
  my $PostsYear = shift;
  my $PostsMonth = shift;
  my $PostsDay = shift;
  &WriteLog($LogLevel,2, "Looking for posts in $PostsDir");
  my @Posts;
  opendir(POSTS, $PostsDir);
  my @DirectoryContents = readdir(POSTS);
  &WriteLog($LogLevel, 3, "Raw entries in $PostsDir: ".Dumper(\@DirectoryContents));
  closedir(POSTS);
  foreach my $DirectoryItem (@DirectoryContents) {
    my $FullPath = $PostsDir."/$DirectoryItem";
    &WriteLog($LogLevel, 3, "Examining $FullPath");
    next if($DirectoryItem =~ /^\./);
    if( -d $FullPath) {
      &WriteLog($LogLevel, 3, "$FullPath is a directory");
      push(@Posts, &GetPosts($FullPath, $PostsYear, $PostsMonth, $PostsDay));
    } else {
      &WriteLog($LogLevel, 3, "$FullPath is a regular file");
      if($DirectoryItem =~ /\.txt$/i) {
        &WriteLog($LogLevel, 3, "$FullPath is a text file. We want it");
        if($PostsYear) {
          (my $Year, my $Month, my $Day) = &GetPostDate($FullPath);
          &WriteLog($LogLevel, 3, "Checking if $FullPath with year $Year matches year $PostsYear");
          if($PostsMonth) {
            &WriteLog($LogLevel, 3, "Checking if $FullPath with year $Year and month $Month matches month $PostsMonth");
            if($PostsDay) {
              if(($Year eq $PostsYear) && ($Month eq $PostsMonth) && ($Day eq $PostsDay)) {
                push(@Posts, $FullPath);
              };
            } else {
              if(($Year eq $PostsYear) && ($Month eq $PostsMonth)) {
                push(@Posts, $FullPath);
              };
            };
          } else {
            if($Year eq $PostsYear) {
            &WriteLog($LogLevel, 3, "$FullPath has year $Year which matches $PostsYear");
              push(@Posts, $FullPath);
            };
          };
        } else {
          push(@Posts, $FullPath);
        };
      };
    };
  };
  @Posts = sort { [stat($b)]->[9] cmp [stat($a)]->[9] } @Posts;
  return @Posts;
};

###################################################
#
# WriteLog(CurrentLogLevel, LogLevelWanted, Message
#
# Write Message to STDERR if LogLevelWanted is equal
# to or less than CurrentLogLevel
#
# Optionally you can supply a fourth parameter Output
# which is a scalar the message gets appended to
# (handy in case you want to see your error messages
# in html as well as well as dumping them to STDERR)
sub WriteLog{
    my $CurrentLogLevel = shift;
    my $LogLevelWanted = shift;
    my $Message = shift;
    my $Output = shift;
    if($LogLevelWanted <= $CurrentLogLevel) {
        print STDERR "$0:$Message\n";
    };
    if(ref($Output) eq 'SCALAR') {
        $Output .= "$Message\n";
    };
};


sub PadWithChar {
    my $String = shift;
    my $NumChars = shift;
    my $PadChar = shift;
    while(length($String) < $NumChars) {
        $String = $PadChar.$String;
    };
    return $String;
};
1;
