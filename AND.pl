#!/usr/bin/env perl
use strict;
use warnings;

sub parse_what {

}

sub do_how {
}

sub main {
    my $what_fly = './WHAT.fl';
    return (my $do_result = do_how(parse_what(${what_fly})));
}

exit main(${ARGV});
