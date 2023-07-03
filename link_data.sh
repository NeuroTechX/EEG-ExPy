DIR=~/.eegnb
DIR_target=~/eegnb
if [ -d "$DIR" ] 
then
    echo "$DIR exists." 
    if [ -L "$DIR_target" ]
    then
        echo "$DIR_target exists. See below"
        ls -al ~ | grep eegnb
    else
        echo "Creating symbolic link $DIR_target"
        ln -s $DIR $DIR_target
    fi
else
    echo "ERROR: $DIR does not exist"
    echo "Creating $DIR, then linking to $DIR_target"
    mkdir -p $DIR
    ln -s $DIR $DIR_target
fi