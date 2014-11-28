# guildford_challenge

The aim of the guildford challenge is to complete one solve for each official event in which you can attain an average in, with your team, as fast as possible. Only one person needs to complete a solve for each individual event. 
The events are: 2x2, 3x3, 4x4, 5x5, 6x6, 7x7, OH, Feet, Mega, Pyra, Sq-1, Clock, Skewb. A regular team consists of three persons. 
You can watch an example by following the link: https://www.youtube.com/watch?v=JOLhwwYNGVo.

This program can compute the optimal teams for each country. 

### Usage:

You will need Python 3.3 or newer. 

* Find the top teams for Finland:

        python guildford_challenge.py --country=Finland
        
* Create a country ranking:

        python guildford_challenge.py --country=countries
        
* Find the top teams for USA using the mini guildford challenge:

        python guildford_challenge.py --country=USA --events="555 444 333 222 333oh sq1 pyram minx clock skewb"
        
* Create a country ranking for 2-person teams using only the events feet, 666 and 777:

        python guildford_challenge.py --country=countries --size=2 --events="333ft 666 777"
        
* Find the top 5 teams for UK:

        python guildford_challenge.py --country="United Kingdom" --number=5
        
* Find the top teams in the world

        python guildford_challenge.py --country=world
        

### License

Copyright (C) 2014 Jakob Kogler, [MIT
License](https://github.com/jakobkogler/guildford_challenge/blob/master/LICENSE.txt)
