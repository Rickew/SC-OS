# SC-OS
This is the official usage document for the SC-OS bot, if you want to know how a command is used, what it's meant to do and a bit of details on the arguments for them find that command below.

<br>

# General Command Usage and Nuances
***Most*** commands are done through a discord @user specification.  
***Some*** commands use just a username for the user argument, and will tell you if the username is wrong.  
***Some*** commands do not have arguments, meaning all you have to do is hit enter to use them, they do their own thing.  
***ALL*** commands have a built in error handler that will force the bot to send an error log to the maintaining server, if this happens you will notice the command you are running either tell you it didn't work, or it will loop forever.  
***ALL*** commands should be stable, BUT if they do break, you should contant the bot maintainer about any bugs you find or errors you encounter.  
***ALMOST ALL*** commands involved UID resolution between discord and roblox. This bot only does it's uid collecting at startup (around 4am EST) every day, there is a command to sync uids for a user, but it will only work if they are verified through bloxlink. This was know to be a potential issue, so it is built into the `/roster add` function to sync the uids for the new addition to the roster, which will hopefully make it so manual uid syncing is not needed.

<br>

## Strike Command
Increases the strikes a user has on the roster. Sends a DM to that user informing them of the strike. Replies to the log_link with a confirmation.
- Universal Command
- Channel Locked
- Rank Locked
### Usage
> /strike `[user]` `[log_link]`  
> /strike `@rickew` `<message link>` 

 This can only be used in a division's punishments channel.
### Arguments
> #### user
>- Discord mention of the user you want to strike.  
>ex: @rickew

> #### log_link
>- The message link to the punishment log.  

<br>

## Inactivity Notice Command
Submits an inactivity notice request, or removes it if they have one active, this includes OVERTIME notices.
- Universal Command
- Approval/Denial Support
- Server Locked Except for Directorate
- Conditional Lock
### Usage  
> /inactivity notice

If the user is submitting an Inactivity Notice, a pop up will appear prompting an end date and a reason for the notice.  
Dates entered must be in the mm/dd/YYYY format, and must not be in the past. The command will default this date to the end of the quota cycle for that cycle, for that division.  
i.e. If you submit a date which is in next week's cycle, it will default it to the end of that cycle.

### Conditional Lock
This command will lock out the user if they are trying to submit an Inactivity Notice more than halfway through the cycle, if their quota is incomplete.

<br>

## Inactivity Override Command
Access command for manipulating a users exemption cell, allows the user to remove an exiting OVERTIME or Inactivity Notice, or do a notice for them.
- Universal Command
- Server Locked
- Rank Locked
### Usage
> /inactivity override `[user]`  
> /inactivity override `@rickew`

If you are submitting an Inactivity Notice for someone, a pop up will appear prompting an end date and a reason for the notice.  
Dates entered must be in the mm/dd/YYYY format, and must not be in the past. The command will default this date to the end of the quota cycle for that cycle, for that division.  
i.e. If you submit a date which is in next week's cycle, it will default it to the end of that cycle.

### Arguments
> #### user
>- Discord mention of the user you want to strike.  
>ex: @rickew

<br>

## Quota Settings Command
Settings command for most quota settings in the bot's DB. This includes, a list of NCOs/COs, minutes/events/points quota for all ranks, the ability to switch between
- Universal Command
- Server Based
- Rank Locked
### Usage
> /quota settings 

### Settings Menus
#### Cycle Settings
- Swap between weekly and bi-weekly quota cycles.
- Enable/Disable Points for NCos and COs (Main Force Only).
- Fix cycle time if it's a cycle ahead or behind.
- Add/Remove ranks to the NCO/CO list (ranks affected by points)

#### Rank Specific Quota
- Switch Quota Type between Manual and Auto
- Enable events by setting it to a number above 0, Disable events by setting it to 0
- Enable time quota by setting it to a number above 0, Disable time quota by setting it to 0
- Switch between quota being time AND events, and time OR events (events optional)
- Set the points quota for NCOs/COs

You cannot set points for a rank not listed as an NCO/CO.  
You cannot set the AND OR to AND without first enabling events.

#### Division Wide Quota
- All specified above, but affects all ranks.
- Points are disabled in this menu, everything else works.

<br>

## Quota Reset Command
Reset's a division's roster, and sends the reset statistics to a channel in that server.
- Universal Command
- Server Based
- Rank Locked
- Time Locked
- Division Locked (Disabled atm)

### Usage
> /quota reset

### Locks
- Time lock prevents a reset if it's more than 3 hours before the reset time (12am EST)
- Rank Lock - Main Force is locked to Captain, TFD's are locked to Officer
- Division Lock - Disabled, prevents Majors from doing other resets in other divisions

### Reset Functions
Each Division has it's own function for the quota checks, which allows each division to conduct their roster resets the way they want to.   This is not editable in the Quota Settings command, this is only editable through the maintainer of the bot editing the code.   
Main Force specfically has a few things added to it like automatic promotion notifications, which tell MF officers that a LR is due for a promotion.

### Reset Statistics
When a roster is reset, the statistics embeds are sent to a specified channel, which at the moment must be changed in the code, and sends embeds (formatted decently well despite character limits) with information on who completed quota, who failed, which strike they are on, potentially if their failure results in an exire, etc depending on the division.  

<br>

## Roster Quickedit Command
This command allows the user to edit the minutes/honor/event cells on the roster in bulk, mostly for use after events as rewards for attending, but also serves as a single 
- Universal Command
- Rank Locked
### Usage
> /roster quickedit `[option]` `[add/sub]` `[users]` `[amount]`   
> /roster quickedit `Honor` `Add` `@rickew @example @user` `100` 

### Arguments
> #### option
>- Honor
>- Minutes
>- Events  
> #### addsub
>- Add
>- Subtract  
> #### users
>- discord user @s, no seperator needed, but you should do @ [space] @  
>-ex: @rickew @user
> #### amount
>- an arbitray amount to add/subtract (it's a float for anyone who knows what that is.)  
>ex: 0.5  
>ex: 2  
>ex: 100

<br>

## Roster Add Command
This command adds a user to the roster, with optional rank selection, and OVERTIME notice
- Universal Command
- Rank Locked
- Bloxlink Integration
### Usage
> /roster add `[user]` `[division]` `[rankselect]` `[overtime]`  
> /roster add `@rickew` `Nothing To See Here` `True` `True`

### Arguments
> #### user
>- Discord mention of the user you want to add.  
>ex: @rickew
> #### division
>- Main Force
>- The Crazies
>- The Armed Gentlemen
>- Iron Fist
>- Nothing To See Here
> #### rankselect
> - This is a bool, true or false, either you select a rank or you don't.  
> By default it is set to false.
> #### overtime
> - This is a bool, true or false, either the user is added with an overtime notice,  
> or they aren't. By default it is set to true.

### Bloxlink Integration
This command does an automatic UID sync and updates the bot's database with the uids for that user. This command WILL give you an error if the user is not verified with bloxlink. So make sure they do that first.

<br>

## Roster Delete Command
Deletes a user from the roster.
- Universal Command
- Rank Locked
### Usage
> /roster delete `[user]`
> /roster delete `Rickew`
### Arguments
> #### user
>- Traditional roblox username - Case Sensitive  
>ex: Rickew

This command makes sure to preserve at least 1 cell per rank, or per division between the sperators on each roster.

<br>

## Roster Transfer Command
Transfers a user from 1 roster to another.
- Universal Command
- Rank Locked
### Usage
> /roster transfer `[user]` `[transferto]` `[overtime]`  
> /roster transfer `@rickew` `Nothing To See Here` `True`
### Arguments
> #### user
>- Discord mention of the user you want to add.  
>ex: @rickew
> #### transferto
>- Main Force
>- The Crazies
>- The Armed Gentlemen
>- Iron Fist
>- Nothing To See Here
> #### overtime
> - This is a bool, true or false, either the user is added with an overtime notice,  
> or they aren't. By default it is set to true.

<br>

## Roster Edit Command
allows the editing of the rest of the user cells on the roster, such as activity strikes, removing strikes, editing the notes cell, and marking manual quotas
- Universal Command
- Rank Locked  
### Usage
> /roster transfer `[user]`  
> /roster transfer `@rickew`  
### Arguments
> #### user
>- Discord mention of the user you want to add.  
>ex: @rickew
### Menu GUI
- This menu allows you to adjust some cells that the other commands don't.
#### Rank
- This will change rank, and will move them around on the roster acccordinly.
#### Roster Notes
- This will change the notes cell on the roster to whatever you change it to.  
The default text in the popup is what is currently in the cell.
#### Add Quota Strike
- This will do exactly what you think.
#### Remove Quota Strike
- This will do exactly what you think.
#### Remove Strike
- This will do exactly what you think.
#### Mark Quota
- This will mark quota complete or incomplete, it is disabled if the quota settings are set to auto.

<br>

## Shopitems Edit Command
Allows authorized users to edit the honor shop items.
- Universal Command
- Rank Locked
### Usage  
> /shopitems edit
### Edit Menu GUI
#### Main Menu
- Add an item
- Edit an item
- Remove an item

#### Adding an item
- Prompts you for an item name
- Will then prompt you to select a few different settings
    - Sub-Options  
    This is if the item has sub-options like startergear items
    - Limit & Cooldown
    - Coupons
    - Division Access  
    This is disabled if the item has options
#### Editing an Item
- Prompts you to select an item
- Will then bring you to the Item Edit Menu
    - Add options (if applicable)
        - Prompts you to enter a name and cost
        - Afterwards you will have to select divisional access  
    - Edit options (if applicable)
        - Will prompt selection of the item option
        Brings you to a menu where you can change the Cost, and enable/disable a division's access to the option.
    - Remove options (if applicable)
        - Will prompt selection of the item option
        - Has a confirmation prompt.
    - Change the Cost
    - Change the Limit & Cooldown
        - Enter 0 into the limit to disable the limit, and also the cooldown.
        The cooldown works by limiting how many can be purchased within an x amount of hours.  
        Once it's been x hours the option will be available for purchase again, but each purchase  has it's own timer.  
        i.e You can't purchase x more after the cooldown runs out, it's individualized.
    - Change Divisional Access
        - Disabled if item has options
        This button brings you to a new menu where you can enable/disable a division's access to the item.
    - Enable/Disable Coupons
#### Remove an Item
- Prompts you to select an item
- Has a confirmation prompt

### Features
- Disabling all divisions will effectively disable an item/option
- Cooldown has a minimum value of 1 hours, if it's set to 0 it'll set the limit to 0, and vise versa.
- Minimum honor cost is 10 fo0r all items and options.
- An item with coupons on, will be affected by discounts, sales, and coupons all the same.

### All changes must be saved, and the menu gui has a timeout of 100 seconds, so don't forget to hit save!

<br>

## Shopitems View Command
Allows regular users to view the honor shop items.
- Universal Command
- Division Locked
### Usage  
> /shopitems view

### Division Locking
Basically, this command will only show a user the item's they have available for purchase. If an item/option is locked to a different division, say Main Force has a weapon The Crazies don't, it will show up for a user in Main Force, but not for a user in The Crazies. This can be adjusted in the shopitems edit command.

### Menu
- Shows all Items
- Select view options to view item options for items that have options.

<br>

## User Info Command
Displays roster information about yourself, or another user.
- Universal Command
### Usage 
> /user info `[user]`  
> /user info `@rickew`
### Arguments
> #### user
>- Discord mention of the user you want to add.  
>ex: @rickew  
this is an OPTIONAL argument, and is set to None by default.  
If this is not specified it will show user info of the person using the command.  

<br>

## User Syncuids Command
This is a developer command, and should only really need to be used by the dev, however if access is needed, it has an enabled users list, which will allow the use of the command.
- Universal Command
- ID Locked
### Usage
> /user syncuids `[user]`  
> /user syncuids `@rickew`
### Arguments
> #### user
>- Discord mention of the user you want to add.  
>ex: @rickew

<br>

## User Discrempancy Command
This is an officer command used to show discrempancies in membership of users, between the group, discord, and roster.
- Universal Command
- Rank Locked
### Usage
> /user discrempancy  
### Nuances
This command was written to serve as a BARE BONES type of assistance. There is hardly any actual parsing done, it only TRIES to guess if someone is a recruit, and it does not tell you a ton of information other than the discrempancy of a user's membership between the group-discord-roster.  
This command should be used by officers in conjunction with researching WHY someone isn't in something. They could have discharged, maybe they are a recruit that never joined the discord, maybe someone forgot to remove them from the roster, it will NOT tell you these things, you must figure them out yourself. However, this assistance is still better than none.

<br>

## User BGC Command (background check)
This command is mostly meant for use by TFDs to do a simple, yet decent background check on users trying to join either mid tryout, or post tryout. This command is far from an exhaustive background check, see details below.
- Universal Command
- Rank Locked
### Usage
> /user bgc `[user]` `[badgegraph]` `[extended]`  
> /user bgc `Rickew` `True/False` `True/False`
### Arguments
> #### user
>- Traditional roblox username - Case Sensitive  
>ex: Rickew
> #### badgegraph
> - This is a bool, it's either true or false, it either displays a graph or doesn't.  
> By default this is set to false. This is because the badge graph is really just an assistance is spotting an alt, and is NOT an actual indicator of an alt account.  
Thie big reason this is default false though is because doing the badge graph is super intensive if the user has a lot of badges and can take anywhere between 20 seconds and 2 minutes to actually work.  
**Unless you suspect the account is an ALT, do not use the badgegraph.**
> #### extended
> - This is a bool, it's either true or false, it either does the extended checks or it doesn't.  
> From what I can tell this isn't too api heavy YET, but it will print out embeds with their groups, the total members in that group, their rank in that group, and specify if they are the lowest rank in that group.  
 **This is essecialy more alt checking, but is most certainly not an indication of an alt account.**

### Checks
- Checks the Rotector Database for a user's status as an ERP associated **FREAK** of an account
- Displays extra information about the user
    - previous username
    - account creation date
    - display name
- NC groups and Ranks
- Checks SC/RW blacklist roster for current and previous usernames
- Checks NC Class-E trello for current and previous usernames
- Optionally displays a badge graph for alt detection assistance.
### Things this does NOT check
- Behavior patterns in servers (toxicity)
- Warnings in NC servers
- Bans in NC servers
- Prior punishments in SC/RW
- Punishments in any other Department
- Reputation within NC  

These all must be checked yourself if you care to. However the list of things checked is a good baseline.
### Rotector Disclaimer
This is a new extension, which has an api which this bot uses to check their database. This is not a be all end all, but can be useful. From research into Rotector done by Rickew, it's an OKAY source, and most of the checking is done by AI, however accounts are user reviewed at some point. Accounts that have only been reviewed by AI and are marked unsafe will be specified as only reviewed by AI.  
At this moment, Rotector is an alright source, and that is why it has been included in this bot. I would prefer to get something like Rocleaner from rubensim, since i find rubensim to be a trustworthy developer considering his history and motivations, but this will have to do.  
Rotector should not be used to deny someone from joining a division unless you manually do your own review first. Do not trust 100 percent what the database says, and make your own judgement.

<br>

## User Nametransfer Command
This is used to switch the username of a person on the roster, and to hopefully sync their new id with the bot.
- Universal Command
- Rank Locked
### Usage
> /user nametransfer `[old]` `[new]`  
> /user nametranfser `Rickew` `foobar123`
### Arguments
> #### currentuser
> - The current or "old" username
> #### newuser
> - The new username

<br>

## Coupon Command
This command can create a coupon for 1 or more SC to use in the Honor Shop for a specific item.
- Main SC Server Locked
- Rank Locked
### Usage
> /coupon `[item]` `[discount]`  
> /coupon `itemname` `20%`
### Arguments
> #### item
> - Select from a list of all items with coupons enabled
> #### discount
> - Select from a list of predefined discounts between 10 - 40 percent

<br>

## Shop Command
This is the Honor Shop Command. All items get sent to the Main SC Honor Shop Channel for approval/fullfilment, and can also be denied.
- Universal Command
- Server Locked
- Automatic Coupon/Discounts/Sales Application
### Usage
> /shop `[item]` `[usercoupons]`  
> /shop `itemname` `True/False`
### Arguments
> #### item
> - Select from a list of items available for pruchase for your division.
> #### usercoupons
> - This is a bool, it is either true or false, either coupons are automatically applied or they aren't.  
If you choose to apply coupons it will check for the oldest active coupon you have for that item and apply it, coupons do not stack.

### Automatic Application of Coupons, Discounts, and Sales
Discounts and Sales are automatically applied, and coupons can be applied on top of them.  
These are applied in a sequencial order, not added up then applied all at once, you **WILL NEVER** hit 100 percent off.  
Discounts and Sales are stored in a database file, and can't be accessed by the bot.

<br>

## Points NCO Command
This command allows the editing of points for an NCO on the Roster.
- Server Locked (Main SC)
- Rank Locked
### Usage
> /points nco `[user]` `[category]` `[addsub]` `[amount]`  
> /points nco `@rickew` `category` `Add` `1`
### Arguments
> #### user
>- Discord mention of the user you want to add.  
>ex: @rickew
> #### category
> - Select from a list of categories of points
> #### addsub
> - Add
> - Subtract
> #### amount
> - An arbitray amount to add/subtract (it's a float for anyone who knows what that is.)  
> ex: 0.5  
> ex: 2  
> ex: 100

<br>

## Points Officer Command
This command allows the editing of points for an officer on the Roster.
- Server Locked (Main SC)
- Rank Locked
### Usage
> /points officer `[user]` `[category]` `[addsub]` `[amount]`  
> /points officer `@rickew` `category` `Add` `1`
### Arguments
> #### user
>- Discord mention of the user you want to add.  
>ex: @rickew
> #### category
> - Select from a list of categories of points
> #### addsub
> - Add
> - Subtract
> #### amount
> - An arbitray amount to add/subtract (it's a float for anyone who knows what that is.)  
> ex: 0.5  
> ex: 2  
> ex: 100

<br>

## Points View Command
View the points of an NCO or Officer.
- Server Locked (Main SC)
### Usage
> /points officer `[user]`  
> /points officer `@rickew` 
### Arguments
> #### user
>- Discord mention of the user you want to add.  
>ex: @rickew

<br>

## Points Refresh Command
Refresh the Catergories for NCO and CO Roster.
- Server Locked (Main SC)
- Rank Locked
### Usage
> /points refresh  

This allows Captain+ To change up the categories of events/tasks that are on the roster, and push those changes to the bot.

<br>

## NTSH Blacklist Add Command
Adds a blacklist to the NTSH Blacklist Embed, also the ability to edit the blacklists already on the roster.
- NTSH Command
- Rank Locked
### Usage
> /ntshblacklist add `[user]` `[reason]` `[length]` `[custom]` `[auth]`
> /ntshblacklist add `foobar` `bad!` `Permanent` `Rickew`
### Arguments
> #### user
>- Traditional roblox username - Case Sensitive  
>ex: Rickew
> #### reason
> - Enter the reason for the blacklist.
> #### length
> - Select an option from the list.
> #### custom
> - if length is set to custom, enter a custom length.
> #### auth
> - Enter the name of the person who authorized the blacklist.
> - Locked to TFL

### Editing Blacklists
To edit a blacklist, this command can be used to "update" the blacklist, just re-enter all the details and change whatever needs to be changed.   
Locked to TFL+

<br>

## NTSH Blacklist Appeal Command
Marks the blacklist as appealed.
- NTSH Command
- Rank Locked
### Usage
> /ntshblacklist appeal `[user]` `[auth]`
> /ntshblacklist appeal `foobar` `Rickew`
### Arguments
> #### user
>- Traditional roblox username - Case Sensitive  
>ex: Rickew
> #### auth
> - Enter the name of the person who authorized the blacklist.
> - Locked to TFL
### Removing an Appeal
Use the NTSH Blacklist Add command to reapply a blacklist to someone who is appealed.

<br>

## NTSH Blacklist Remove Command
Removes the blacklist from the embed.
- NTSH Command
- Rank Locked
### Usage
> /ntshblacklist remove `[user]`
> /ntshblacklist remove `foobar`
### Arguments
> #### user
>- Traditional roblox username - Case Sensitive  
>ex: Rickew

<br>

## NTSH Hit Send Command
Places a hit on someone.
- NTSH Command
- Internal Regulations
> /hit send `[user]` `[num]` `[reason]` `[bounty]` `[style]` `[expiration]` `[ping]` `[authorization]`  
> /hit send `Rickew` `1` `Because` `300` `Normal` `3d` `False` `Rickew`
### Arugments
> #### user
>- Traditional roblox username - Case Sensitive  
>ex: Rickew
> #### num
> - The number of hits
> #### reason
> - The reason for the hits
> #### bounty
> - The amount of honor awarded per hit
> #### style
> - Select from the predefined list.
> - By default it is the Normal Style.
> #### expiration
> - enter "Never" for no expiration or one of the following: #y #m #w #d in a sequence for years, months, weeks, and days."
> - By default it is set to 1 week
> #### ping
> - This is a bool, it is either true or false, either it will ping for the hit or it will not.
> - Set to False by default.
> #### authorization
> - The user who authorized the hit
> - by default it is the person using the command.

<br>

## NTSH Hit Update Command
Update an existing hit.
- NTSH Command
- Internal Regulations
> /hit send `[targetname]` `[newname]` `[reason]` `[bounty]` `[style]` `[expiration]` `[authorization]`  
### Arugments
All arguments are optional, because they all change something about the hit embed and can be used entirely seperately from each other.
> #### targetname
> - Traditional roblox username - Case Sensitive  
>ex: Rickew  
> If you're using this command outside of a hit-thread, this will find the oldest active hit for that person and make changes to that one. If this is not specified, you must be using the command in a thread, and all change will be made to that hit.
> #### amount
> - The number of hits
> - This must be specified as x/x or just a number xx, all other input will be ignored.
> #### reason
> - The reason for the hits
> #### bounty
> - The amount of honor awarded per hit
> #### style
> - Select from the predefined list, will change it to that selection.
> #### expiration
> - enter "Never" for no expiration or one of the following: #y #m #w #d in a sequence for years, months, weeks, and days."
> #### status
> - Incomplete
> - Complete
This will archive the hit as completed.
> - In Progress
> - Revoked
This will archive the hit as revoked.
> #### authorization
> - The user who authorized the hit

<br>

## NTSH Hit Delete Command
Deletes a hit thread
- NTSH Command
- Internal Setup for Rank Lock
### Usage
> /hit delete  

This will delete the hit-thread after a confirmation prompt pops up to confirm you want to delete the thread. This command is mostly just to be used in case of accidents in using something like the hit send command.

<br>

# Accepting Inactivity Notices
There will be buttons underneath Inactivity Notice Requests.
These are rank locked to Security Supervisor+.
Once it is accepted/denied the user will recieve a DM letting them know.

# Honor Shop Buttons
Similar to the Inactivity Notice Request buttons, there will be an accept and deny button, except these are locked to Security Supervisor AND Class-Os for in-game fullfillment. 

# Honor Shop Hits
If a hit is purchased, it will go straight to NTSH. There will be no confirmation if it is accepted, there will be no confimration if it's completed. Username mispellings are fogiven, and you won't have you're honor taken, but if you give them the rank incorrectly, then they will take your honor and still deny the hit.

# NTSH Assassination Shop Item
This item is HARD CODED into the program. It cannot be removed. If you want to though, it can be disabled for all divisions, effectively removing it.