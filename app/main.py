from app.agent.graph import app

def main():
	"""Main function to run the interactive warranty agent."""
	print("🤖 Warranty Agent is ready. Type 'exit' to quit.")
    
	# Maintain a simple chat history for the session
	chat_history = []
    
	while True:
		user_input = input("You: ")
		if user_input.lower() in ['exit', 'quit']:
			print("Goodbye!")
			break
        
		# Define the initial state for the graph
		initial_state = {
			"user_query": user_input,
			"chat_history": chat_history,
		}
        
		# Invoke the agent
		final_state = app.invoke(initial_state)
		response = final_state.get('response', "Sorry, I encountered an error.")
        
		# Print the response and update history
		print("Agent:", response)
		chat_history.append((user_input, response))

if __name__ == "__main__":
	main()
