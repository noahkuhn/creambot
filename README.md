# C.R.E.A.M. Bot
This is a collection of scripts to do fun things with Python on various blockchains.

Ideally you would install a virtual environment manager. I use [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html), specifically Miniconda. Once you have that installed, you can create a new environment like so:

`$ conda create --name NAME python=VERSION`

Where the NAME is whatever you want to call your environment, and the VERSION is the full version number, like 3.10.8. For example:

`$ conda create --name creambot python=3.10.8`

These scripts have various requirements that will be added to requirements.txt as needed. The requirements vary depending on the script. Once you have your environment set up, make sure you activate it

`$ conda activate NAME`

Once activated, you can use pip to install them like so:

`$ pip install -r requirements.txt`

# Requirements
- Python 3.10.8 (but probably works with most)
- [eth-brownie](https://pypi.org/project/eth-brownie/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)

# Brownie
To do anything with these scripts, you need to set up a wallet address using [Brownie](https://eth-brownie.readthedocs.io/en/stable/).

**Add new account**

`$ brownie accounts generate NAME` 

NAME is the account name you want to use.
You'll need to record the mnemonic and set a password. **Keep these secret, keep these safe**.

Once that is set, you need to send that wallet some ETH so it can transact. Arbitrum gas is pretty cheap, so you can start with $10 or so. Then depending on the bot, you may need to send some other tokens (USDC, WETH, etc).

# Bots
## arbitrum_usdc_weth_swap.py

Simple bot that does a one-way swap from USDC > WETH on Arbitrum. You need to have USDC in your wallet in order to use this.

This is set up such that it could live on a VPS and be called by cron. Thus I have the wallet password set in an .env file so the script can be called without user intervention. You will need to create your own .env file and set two constants. There is an .env-example file that demonstrates this.

- **BROWNIE_ACCOUNT**: the name of the account you created above.
- **BROWNIE_PASSWORD**: the password you set when you created the account.

This isn't the most secure, so if you only intend to call this manually, just omit the password parameter from the brownie.accounts.load call, don't add that line to your .env, and comment out the BROWNIE_PASSWORD constant assignment.

By default this script has a **DRY_RUN** constant set as *True* which means the transaction won't actually submit. In order to really do a swap, you need to set **DRY_RUN** to *False*. Then call it like so:

`$ python arbitrum_weth_usdc_dca.py`

# Cron

So the point of some of these bots is to be able to automatically call them with a Cron job on a VPS, to effectively set up a DCA buy on a schedule of your choosing. In order to make this work with conda environments, you need to set up a simple shell script to activate the environment, call the script, and then deactivate the enivornment.

Create a file in your home directory. Call it whatever you like: **filename.sh**. Then within, add the following. Make sure to set the paths based on your setup.

    #!/bin/bash
    source /PATH_TO_CONDA_BIN/activate ENVIRONMENT_NAME
    python /PATH_TO_SCRIPT/PYTHON_FILENAME.py
    conda deactivate