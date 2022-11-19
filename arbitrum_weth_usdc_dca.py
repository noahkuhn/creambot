import brownie
import time, os, sys

from dotenv import load_dotenv
load_dotenv()

BROWNIE_NETWORK = 'arbitrum-main'

# Set these in an .env file at the same level as this fileconda update -n base -c defaults conda
BROWNIE_ACCOUNT = os.environ['BROWNIE_ACCOUNT']
BROWNIE_PASSWORD = os.environ['BROWNIE_PASSWORD']

# Set your desired swap details here
FEE = 500 # 500, 3000 or 10000 corresponding to 0.05%, 0.3%, or 1.0% pools
AMOUNT = 2 # Amount of tokens to swap. This is all set up for USDC, so this is $x dollars
SLIPPAGE = 0.01 # Percentage of slippage to allow. This determines the minimum amount you'll receive
VERBOSE_PRINTS = True # Prints more details about what is going on.
DRY_RUN = True # Simulate swaps and approvals.

# Set our token contract addresses
USDC_CONTRACT_ADDRESS = '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8'
WETH_CONTRACT_ADDRESS = '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1'

# Set the generic Uniswap Contracts. Not all of these are used
UNISWAPV3_ROUTER2 = '0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45' #SwapRouter02 https://arbiscan.io/address/0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45#code
UNISWAPV3_QUOTER = '0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6' #Quoter https://arbiscan.io/address/0xb27308f9f90d607463bb33ea1bebb41c27ce5ab6#code

def main():
	
	# Connect to the RPC via Brownie
	try:
		print()
		print("RPC:")
		brownie.network.connect(BROWNIE_NETWORK)
		print(" RPC Connected!")
	except:
		sys.exit(
			"Could not connect! Verify your Brownie network settings using 'brownie networks list'"
		)
	
	# Load the account details. Remove the password param if you want to be more secure
	# You will need to enter it on every run. You need to create an account via Brownie
	# and add the name to your .env file as BROWNIE_ACCOUNT. "user" is an arbitrary name
	# for your bot. Cash Rules Everything Around Me.
	try:
		print()
		print("ACCOUNT:")
		user = brownie.accounts.load(BROWNIE_ACCOUNT, password=BROWNIE_PASSWORD)
		print(" Account Loaded!")
	except:
		sys.exit(
			"Could not load account! Verify your Brownie account settings using 'brownie accounts list'"
		)
	
	print()
	print("CONTRACTS:")
	# Create some token objects. If you want to trade different tokens, you will need to 
	# create objects for them in the same format as you see below, add them to the tokens 
	# array, and then use their object names in the swap function
	usdc = getContract(USDC_CONTRACT_ADDRESS)
	weth = getContract(WETH_CONTRACT_ADDRESS)
	
	# Create some Uniswap contract objects
	uniswap_router2 = getContract(UNISWAPV3_ROUTER2)
	uniswap_quoter = getContract(UNISWAPV3_QUOTER)
	
	# Define our pool of routers. Used for approvals
	routers = [
		uniswap_router2,
	]
	
	# Define our pool of tokens. Used for approvals.
	tokens = [
		usdc,
		weth
	]
	
	print(" Contracts Loaded!")
	
	# Confirm approvals for all tokens on all routers
	print()
	if VERBOSE_PRINTS:
		print("APPROVALS:")
		
	for router in routers:
		for token in tokens:
			if token.allowance(user.address, router.address) < token.balanceOf(user.address):
				token.approve(router.address, -1, {'from':user.address})
			else:
				if VERBOSE_PRINTS:
					print(f" {token.name()} on {router} OK")
	print()
	
	
	
	# Lets set up our variables. Constants (FEE, AMOUNT, SLIPPAGE) are set at the top of this file.
	tokenIn = usdc
	tokenOut = weth
	fee = FEE
	recipient = user
	amountIn = AMOUNT * (10 ** tokenIn.decimals())
	sqrtPriceLimitX96 = 0
	deadline = int(time.time()) + 30
	
	tx_params = {
		"from": user.address,
		#"chainId": brownie.chain.id,
		#"gas": TX_GAS_LIMIT,
		#"nonce": recipient.nonce,
	}
		
	input_balance = tokenIn.balanceOf(user.address)
	output_balance = tokenOut.balanceOf(user.address)
	
	if VERBOSE_PRINTS:
		print("BALANCES:")
		print(f' {tokenIn.name()} Swap: {amountIn}')
		print(f' {tokenIn.name()} Balance: {input_balance}')
		print(f' {tokenOut.name()} Balance: {output_balance}')
		print()
			
	if input_balance < amountIn:
		print(f" You don't have enough for this swap. Gotta reload")
		exit()
		
	if VERBOSE_PRINTS:
		print("PARAMETERS:")
		print(f' tokenIn: {tokenIn.name()} {tokenIn.address}')
		print(f' tokenOut: {tokenOut.name()} {tokenOut.address}')
		print(f' fee: {fee} ({fee / 10000}%)')
		print(f' amountIn: {amountIn} ({amountIn / 10**tokenIn.decimals()} {tokenIn.symbol()})')
		print(f' sqrtPriceLimitX96: {sqrtPriceLimitX96}')
	
	# Try to get the swap rate (price). Need to use .call() to simulate this, 
	# as it uses gas to call quoteExactInputSingle directly
	try:
		
		amountOutMinimum = uniswap_quoter.quoteExactInputSingle.call(
			tokenIn.address,
			tokenOut.address,
			fee,
			amountIn,
			sqrtPriceLimitX96,
		)
	
	# No good, query failed for some reason
	except Exception as e:
		print(f"PRICE QUERY FAILED: {e}")
		
	# Success, we got the swap rate (price)
	else:
		if VERBOSE_PRINTS:
			print(f" amountOutMinimum: {amountOutMinimum} ({amountOutMinimum / 10**tokenOut.decimals()} {tokenOut.symbol()})")
		
		# Encode all our variables to the format expected by the multicall function
		payload_data = uniswap_router2.exactInputSingle.encode_input(
			(
				tokenIn.address,
				tokenOut.address,
				fee,
				recipient.address,
				amountIn,
				amountOutMinimum * (1-SLIPPAGE),
				sqrtPriceLimitX96,
			)
		)
		
		# Lets try to make our swap
		try:
			
			# If it's a real swap, submit it
			if not DRY_RUN:
				print()
				print("SENDING TRANSACTION")
				
				# Submit our transaction
				uniswap_router2.multicall['uint256,bytes[]'](
					deadline,
					[payload_data],
					tx_params
				)
			# Placeholder for Dry Run	
			else:
				print()
				print(f"DRY RUN TRANSACTION:")
		
		# Bad news, something went wrong	
		except Exception as e:
			print()
			print(f"TRANSACTION FAILED: {e}")
			print()
		
		# Good news, transaction sent to blockchain!	
		else:
			print()
			print("!!!TRANSACTION SENT!!!")
			print()

def getContract(address):
	try:
		contract = brownie.Contract(
			address,
		)
	except:
		contract = brownie.Contract.from_explorer(
			address,
		)
	return contract

if __name__ == '__main__':
	main()