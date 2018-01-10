#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2012 Sander van Noort <vanNoort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Build lilypond files"""

import io
import re
import sys  # pylint: disable=W0611
import configobj
import os
import logging

from mconvert import tools

ORIG = "text/lilypond-template"
DEST = "text/lilypond-score", "text/lilypond-midi"
CONVERT = "lyt_ly"
ROOT = os.path.dirname(__file__)
logger = logging.getLogger(__name__)
cache = tools.Cache()


def lyt_ly(orig, dest, *_args, **kwargs):
    """Convert lilypond template to lilypond"""

    ftypes = kwargs.get("tree").items[kwargs.get("step")]["ftypes"]
    midi = True if "text/lilypond-midi" in ftypes else False
    values = configobj.ConfigObj(os.path.join(ROOT, "lily.ini"))
    values.update(configobj.ConfigObj(orig))

    for key in values.keys():
        values[key] = (update_dynamics(values[key], values, midi)
                       if "dynamics" in key else
                       update_score(values[key]))

    parts = tools.SetList(
        [cache.output.group(2)
         for key in values.keys()
         if cache(re.match("(lower|upper|dynamics)(.*)", key)) and
         cache.output.group(2) not in ["Options"]])

    tools.create_dir(dest, is_file=True)
    with io.open(dest, "w") as fobj:
        fobj.write("""\\version "2.14.2"
        \\pointAndClickOff
        \\include "articulate.ly"
        """)
        for key, value in values.items():
            if key == "header":
                fobj.write("""\\header {{
                    {value}
                    tagline=##f
                    }}
                    """.format(value=value))
            elif "Options" not in key:
                fobj.write("{0} = {1}\n".format(key, value))

        if midi:
            fobj.write(get_midi_score(values, parts))
        else:
            for counter, part in enumerate(parts):
                fobj.write(get_score(
                    values,
                    part,
                    True if counter == len(parts) - 1 else False))
            fobj.write("""\\paper {{
                {options}
                }}
                """.format(options=values.get("paperOptions", "")))
    return dest


def update_dynamics(dynamics, values, midi):
    """Update the specific dynamic key"""

    def replace_dynamic(match):
        """Replace p_[dolce] to p text{dolce}"""
        beat, dynamic, text = match.groups()
        var = re.sub("[^a-z]", "", "{0}{1}".format(dynamic, text))
        if midi:
            return (beat if dynamic == "" else
                    "{0}\\{1}".format(beat, dynamic))

        if var not in values:
            values[var] = (
                "#(make-dynamic-script\n" +
                "   #{{ \\markup {{ \\dynamic {dynamic} \\normal-text" +
                "   \\italic \\whiteout \"{text}\"}} #}})").format(
                    dynamic=dynamic, text=text)
            # values[var] = """#(make-dynamic-script (markup #:line (
            #     #:dynamic "{dynamic}"
            #     #:normal-text #:italic
            #     "{text}"
            #     )))""".format(dynamic=dynamic, text=text)
            values.scalars.sort(key=lambda x: 0 if x == var else 1)

        return "\\leftAlign {0}\\{1}".format(beat, var)

    dynamics = re.sub(
        r"(s[0-9\.^_-]*)\\([pfms]*)\[(.*?)\]",
        replace_dynamic,
        dynamics)

    return dynamics


def update_score(score):
    """Update some macros in the scores"""

    def replace_text(match):
        """Put text above or below"""
        return """\\once \\override Score.RehearsalMark
                #'break-visibility = #begin-of-line-invisible
           \\once \\override Score.RehearsalMark
               #'direction = #{direction}
           \\once \\override Score.RehearsalMark
               #'self-alignment-X = #RIGHT
           \\mark \\markup{{\\italic "{text}"}}
            """.format(direction=match.group(1).upper(),
                       text=match.group(2))

    score = re.sub(
        r"\\(up|down)_right\[(.*)\]",
        replace_text,
        score)

    return score


def get_midi_score(values, parts):
    """Get the score for a pdf"""

    output = """\\score{
        \\unfoldRepeats
        \\articulate
        \\new PianoStaff = "PianoStaff_pf" <<
        """

    for name in ["upper", "lower"]:
        output += (
            """\\new Staff = \"{name}\" <<
            {{ {dynamics} }}
            {{ {pedal} }}
            {{ {score} }}
            >>
            """).format(
                name=name.title(),
                dynamics=" ".join([
                    "\\dynamics{0}".format(part) for part in parts
                    if "dynamics" + part in values]),
                pedal=" ".join([
                    "\\pedal{0}".format(part) for part in parts
                    if "pedal" + part in values]),
                score=" ".join([
                    "\\{0}{1}".format(name, part) for part in parts
                    if name + part in values]))
    output += """>>
        \\midi {{ {options} }}
        }}
        """.format(options=values.get("midiOptions", ""))
    return output


def get_score(values, part, last):
    """Get the score for a pdf"""

    output = """
        \\score{
            \\new PianoStaff = "PianoStaff_pf" <<
                #(set-accidental-style 'piano-cautionary)
        """
    if "upper" + part in values:
        output += """\\new Staff = "Upper" << {{
                {options_part}
                {options}
                \\upper{part}
                \\bar {bar}
            }} >>
            """.format(options_part=values.get("upperOptions" + part, ""),
                       options=values.get("upperOptions", ""),
                       part=part,
                       bar="\"|.\"" if last else "\"||\"")
    if "dynamics" + part in values:
        output += """\\new Dynamics = "Dynamics" {{
                {options_part}
                {options}
                \\dynamics{part}
            }}
            """.format(options_part=values.get("dynamicsOptions" + part, ""),
                       options=values.get("dynamicsOptions", ""),
                       part=part)
    if "lower" + part in values:
        output += """\\new Staff = "Lower" << {{
                {options_part}
                {options}
                \\lower{part}
                \\bar {bar}
            }} >>
            """.format(options_part=values.get("lowerOptions" + part, ""),
                       options=values.get("lowerOptions", ""),
                       part=part,
                       bar="\"|.\"" if last else "\"||\"")
    if "pedal" + part in values:
        output += """
            \\new Dynamics = "Pedal" {{
                \\pedal{part}
            }}
            """.format(part=part)
    output += ">>\n"
    output += """\\header {
        title = ##f
        opus = ##f
        }
        """
    output += """\\layout {{
            {options}
            {options_part}
        }}
        """.format(options_part=values.get("layoutOptions" + part, ""),
                   options=values.get("layoutOptions", ""))

    output += "}\n"
    return output
