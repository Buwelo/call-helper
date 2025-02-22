import difflib
import logging
from datetime import datetime
import re


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_time(time_str):
    """Convert SRT timestamp to seconds"""
    time_obj = datetime.strptime(time_str.replace(',', '.'), '%H:%M:%S.%f')
    return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second + time_obj.microsecond / 1000000


def extract_text_from_srt(srt_content):
    """Extract only the text content from SRT format, ignoring timestamps and sequence numbers"""
    lines = srt_content.split('\n')
    text_lines = []
    for line in lines:
        if not re.match(r'^\d+$', line) and not re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', line) and line.strip():
            text_lines.append(line.strip())
    return ' '.join(text_lines)


def compare_transcript(good_transcript, bad_transcript):
    good_text = extract_text_from_srt(good_transcript)
    bad_text = extract_text_from_srt(bad_transcript)

    if good_text == bad_text:
        return 'Transcripts are identical'

    d = difflib.Differ()
    diff = list(d.compare(good_text.split(), bad_text.split()))

    # Group differences for better readability
    grouped_diff = []
    current_good_group = []
    current_bad_group = []

    for line in diff:
        if line.startswith('  '):  # unchanged
            if current_good_group or current_bad_group:
                if current_good_group:
                    grouped_diff.append(
                        "CORRECT: " + ' '.join(current_good_group))
                if current_bad_group:
                    grouped_diff.append(
                        "USER   : " + ' '.join(current_bad_group))
                current_good_group = []
                current_bad_group = []
            grouped_diff.append(line[2:])
        elif line.startswith('- '):  # in good_transcript
            current_good_group.append(line[2:])
        elif line.startswith('+ '):  # in bad_transcript
            current_bad_group.append(line[2:])

    # Add any remaining groups
    if current_good_group:
        grouped_diff.append("CORRECT: " + ' '.join(current_good_group))
    if current_bad_group:
        grouped_diff.append("USER   : " + ' '.join(current_bad_group))

    return '\n'.join(grouped_diff)


EXAMPLE_COMPARISON_RESULT = """CORRECT: 1 00:00:01,220 --> 00:00:03,420
(Transcribed
by
TurboScribe.ai.
Go
Unlimited
to
remove
this
message.)
Once
upon
a
time,
there
were
four
little
CORRECT: 2 00:00:03,420 --> 00:00:07,980
rabbits,
and
their
names
were
Fopsie,
Mopsie,
Cottontail,
CORRECT: 3 00:00:08,240 --> 00:00:08,560 and Peter. 4 00:00:09,560 --> 00:00:11,620
They
lived
with
their
mother
in
a
sandbank,
CORRECT: 5 00:00:11,760 --> 00:00:14,000
underneath
the
root
of
a
very
big
fir
CORRECT: 6 00:00:14,000 --> 00:00:14,280 tree. 7 00:00:15,379 --> 00:00:18,880
Now,
my
dears,
said
old
Mrs.
Rabbit
one
CORRECT: 8 00:00:18,880 --> 00:00:21,460
morning,
you
may
go
into
the
fields
or
CORRECT: 9 00:00:21,460 --> 00:00:24,380
down
the
lane,
but
don't
go
into
Mr.
CORRECT: 10 00:00:24,720 --> 00:00:25,140
McGregor's
garden.
CORRECT: 11 00:00:25,900 --> 00:00:27,860
Your
father
had
an
accident
there,
he
was
CORRECT: 12 00:00:27,860 --> 00:00:29,420
put
in
a
pie
by
Mrs.
McGregor.
CORRECT: 13 00:00:30,280 --> 00:00:32,560
Now,
run
along,
and
don't
get
into
mischief,
CORRECT: 14 00:00:32,960 --> 00:00:33,760
I'm
going
out.
CORRECT: 15 00:00:34,820 --> 00:00:37,320
Then,
old
Mrs.
Rabbit
took
a
basket
and
CORRECT: 16 00:00:37,320 --> 00:00:38,760
her
umbrella
to
the
baker's.
CORRECT: 17 00:00:39,460 --> 00:00:42,480
She
brought
a
loaf
of
brown
bread
and
CORRECT: 18 00:00:42,480 --> 00:00:43,740
five
currant
buns.
CORRECT: 19 00:00:44,760 --> 00:00:47,380
Fopsie,
Mopsie,
and
Cottontail,
who
were
good
little
CORRECT: 20 00:00:47,380 --> 00:00:49,740
bunnies,
went
down
to
the
lane
to
gather
CORRECT: 21 00:00:49,740 --> 00:00:50,340
blackberries.
CORRECT: 22 00:00:51,040 --> 00:00:53,520
But
Peter,
who
was
very
naughty,
ran
straight
CORRECT: 23 00:00:53,520 --> 00:00:56,340
away
to
Mr.
McGregor's
garden
and
squeezed
under
CORRECT: 24 00:00:56,340 --> 00:00:56,680
the
gate.
CORRECT: 25 00:00:57,720 --> 00:01:00,960
First,
he
ate
some
lettuces
and
some
French
CORRECT: 26 00:01:00,960 --> 00:01:04,880
beans,
and
then
he
ate
some
radishes.
CORRECT: 27 00:01:05,480 --> 00:01:07,400
And
then,
feeling
rather
sick,
he
went
to
CORRECT: 28 00:01:07,400 --> 00:01:08,980
look
for
some
parsley.
CORRECT: 29 00:01:09,800 --> 00:01:13,400
But,
around
the
end
of
a
cucumber
frame,
CORRECT: 30 00:01:14,020 --> 00:01:17,040
whom
should
he
meet
but
Mr.
McGregor?
CORRECT: 31 00:01:17,440 --> 00:01:19,360
Mr.
McGregor
was
on
his
hands
and
knees,
CORRECT: 32 00:01:19,940 --> 00:01:21,900
planting
out
young
cabbages.
CORRECT: 33 00:01:21,900 --> 00:01:24,460
But
he
jumped
up
and
ran
after
Peter,
CORRECT: 34 00:01:24,540 --> 00:01:27,320
waving
a
rake
and
calling
out,
Stop
thief!
CORRECT: 35 00:01:28,140 --> 00:01:29,860
Peter
was
most
dreadfully
frightened.
CORRECT: 36 00:01:30,380 --> 00:01:33,800
He
rushed
all
over
the
garden,
for
he
CORRECT: 37 00:01:33,800 --> 00:01:35,260
had
forgotten
the
way
back
to
the
gate.
CORRECT: 38 00:01:35,740 --> 00:01:37,240
He
lost
one
of
his
shoes
among
the
CORRECT: 39 00:01:37,240 --> 00:01:39,940
cabbages
and
the
other
shoe
amongst
the
potatoes.
CORRECT: 40 00:01:40,500 --> 00:01:42,320
After
losing
them,
he
ran
on
four
legs
CORRECT: 41 00:01:42,320 --> 00:01:44,800
and
went
faster,
so
that
he
might
have
CORRECT: 42 00:01:44,800 --> 00:01:48,000
got
away
altogether
if
he
had
not
unfortunately
CORRECT: 43 00:01:48,000 --> 00:01:50,200
ran
into
a
gooseberry
net
caught
by
the
CORRECT: 44 00:01:50,200 --> 00:01:51,440
large
buttons
on
his
jacket.
CORRECT: 45 00:01:52,120 --> 00:01:54,000
It
was
a
blue
jacket
with
brass
buttons,
CORRECT: 46 00:01:54,280 --> 00:01:54,740
quite
new.
CORRECT: 47 00:01:55,720 --> 00:01:58,000
Peter
gave
himself
up
for
lost,
shed
big
CORRECT: 48 00:01:58,000 --> 00:02:00,720
tears,
but
his
solids
were
overheard
by
some
CORRECT: 49 00:02:00,720 --> 00:02:02,940
friendly
sparrows,
who
flew
to
him
in
great
CORRECT: 50 00:02:02,940 --> 00:02:05,560
excitement
and
implored
him
to
exert
himself.
CORRECT: 51 00:02:06,420 --> 00:02:08,919
Mr.
McGregor
came
up
with
a
sieve,
which
CORRECT: 52 00:02:08,919 --> 00:02:11,380
he
intended
to
pop
upon
the
top
of
CORRECT: 53 00:02:11,380 --> 00:02:11,600 Peter. 54 00:02:12,160 --> 00:02:14,420
But
Peter
wriggled
out
just
in
time,
leaving
CORRECT: 55 00:02:14,420 --> 00:02:18,180
his
jacket
behind
him,
and
rushed
into
the
CORRECT: 56 00:02:18,180 --> 00:02:19,780
tool
shed
and
jumped
into
a
can.
CORRECT: 57 00:02:20,480 --> 00:02:21,740
It
would
have
been
a
beautiful
thing
to
CORRECT: 58 00:02:21,740 --> 00:02:24,180
hide
in
if
it
had
not
had
so
CORRECT: 59 00:02:24,180 --> 00:02:25,460
much
water
in
it.
CORRECT: 60 00:02:26,240 --> 00:02:28,120
Mr.
McGregor
was
quite
sure
that
Peter
was
CORRECT: 61 00:02:28,120 --> 00:02:31,440
somewhere
in
the
tool
shed,
perhaps
hidden
underneath
CORRECT: 62 00:02:31,440 --> 00:02:32,060
a
flower
pot.
CORRECT: 63 00:02:32,400 --> 00:02:34,020
He
began
to
turn
them
over
carefully,
looking
CORRECT: 64 00:02:34,020 --> 00:02:34,540
under
each.
CORRECT: 65 00:02:35,320 --> 00:02:37,500
Presently,
Peter
sneezed.
CORRECT: 66 00:02:38,100 --> 00:02:38,660
Curty
shoe!
CORRECT: 67 00:02:39,520 --> 00:02:41,720
Mr.
McGregor
was
after
him
in
no
time,
CORRECT: 68 00:02:41,920 --> 00:02:43,540
and
tried
to
put
his
foot
upon
Peter,
CORRECT: 69 00:02:43,700 --> 00:02:45,840
who
jumped
out
of
a
window,
upsetting
three
CORRECT: 70 00:02:45,840 --> 00:02:46,220
plants.
CORRECT: 71 00:02:47,120 --> 00:02:48,900
The
window
was
too
small
for
Mr.
McGregor,
CORRECT: 72 00:02:49,500 --> 00:02:50,960
and
he
was
tired
of
running
around
after
CORRECT: 73 00:02:50,960 --> 00:02:51,180 Peter. 74 00:02:52,160 --> 00:02:53,400
He
went
back
to
his
work.
CORRECT: 75 00:02:54,000 --> 00:02:54,960
Peter
sat
down
to
rest.
CORRECT: 76 00:02:55,560 --> 00:02:57,180
He
was
out
of
breath
and
trembling
with
CORRECT: 77 00:02:57,180 --> 00:02:59,180
fright,
and
he
had
not
the
least
idea
CORRECT: 78 00:02:59,180 --> 00:02:59,900
which
way
to
go.
CORRECT: 79 00:03:00,600 --> 00:03:02,920
Also,
he
was
very
damp,
with
sitting
in
CORRECT: 80 00:03:02,920 --> 00:03:03,320 that can. 81 00:03:03,320 --> 00:03:05,520
As
your
time
you
began
to
wander
about,
CORRECT: 82 00:03:05,820 --> 00:03:08,200
going
lippity-lippity,
not
very
fast,
and
looking
CORRECT: 83 00:03:08,200 --> 00:03:08,720
all
around."""

