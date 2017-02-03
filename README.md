KINDEN VIETNAM Customize & Deploy OpenERP 7
===========================================

### General information about KDVN OpenERP 7

KINDEN VIETNAM OpenERP 7 customization modules.

1. Project & Contract

2. Purchase Orders

3. Expenses

4. Material Price

5. Stock Management

6. Asset and Fixed Asset Control

7. General Expenses

8. Additional Tools

### Ready to use docker-compose file

This repository included a docker-compose.yml file that ready to use with the command **`docker-compose up`**
*Some notes:*

* General ways to commit code
    * Forked this repository
    * Switch to branch oe7-develop
    * Read the repository issues and comment one that you want to work on that
    * Coding or Add new one
    * Push the code and make a **pull request**

* If cloning the repository, the customized addons, follow instruction below
    * goto github.com to common repository, fork repository
    * git init
    * git remote add origin *your forked repository url*
    * git fetch
    * git branch oe7-develop origin/oe7-develop
    * git checkout oe7-develop

* If push your changing to common repository
    * goto your forked repository click pull request -> create pull request

* Get the latest code from common repository
    * Add upstream to your working git folder (one time only)
        * git remote add upstream https://www.github.com/kdvn/openerp7
        * git fetch --all
        * git merge upstream/oe7-develop (Note: Must working on your branch you want to get the latest code)
        * git push

* Using pgtool.bash to dump or restore a database (**on real machine running docker**) (This tool only running on linux)
    * Restore a database
        * **`./pgtools.bash -C=NameOfDatabaseContainer -F=PathToFileDatabse -D=NameOfDatabase create`**
        * Before to use pgtools please follow introduction:
            * Download file **pgtools.bash** from this repository.
            * Make file can excuateble **```chmod +x1 pgtools.bash```**
        
* Please note when using docker-compose
    * Port opening (in container) (Already exposed)
        * Port 3000 using for Cloud9 IDE
        * Port 8069 using for OpenERP Web
    * 3 folder can mount (volumes)
        * /mnt/oefilestore: Using filestore for OpenERP
        * /mnt/extra-addons: Other addons using for OpenERP System
        * /opt/workspace: Your workspace
    * *Please change or remove LOCAL_USER_ID, this variable is used to change user id in the container*. Command to get user id **`id -u $USER`** 
    * Passwords showing in the docker-compose.yml file are for demonstration purpose only. They can be changed and **should _NOT_ upload** to github.