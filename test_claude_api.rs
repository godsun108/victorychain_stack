use std::env;
use reqwest::Client;
use serde_json::{json, Value};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🤖 Testing Claude API Integration");
    println!("==================================");
    
    // Load API key from environment
    let api_key = env::var("CLAUDE_API_KEY").expect("CLAUDE_API_KEY not set");
    
    println!("✅ Claude API key loaded (length: {})", api_key.len());
    
    // Test Claude API call
    let client = Client::new();
    
    let request_body = json!({
        "model": "claude-3-haiku-20240307",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": "Analyze Bitcoin (BTC) for short-term momentum trading. Current price change: +3.5% in 24h, volume: $2.1B. Respond with just: BULLISH, BEARISH, or NEUTRAL with confidence 0-100."
            }
        ]
    });
    
    println!("🔄 Testing Claude API call...");
    
    let response = client
        .post("https://api.anthropic.com/v1/messages")
        .header("Authorization", format!("Bearer {}", api_key))
        .header("Content-Type", "application/json")
        .header("anthropic-version", "2023-06-01")
        .json(&request_body)
        .send()
        .await?;
    
    println!("📊 Response Status: {}", response.status());
    
    if response.status().is_success() {
        let response_text = response.text().await?;
        println!("✅ Claude API Response:");
        
        // Try to parse as JSON
        if let Ok(json_response) = serde_json::from_str::<Value>(&response_text) {
            if let Some(content) = json_response["content"].as_array() {
                if let Some(first_content) = content.get(0) {
                    if let Some(text) = first_content["text"].as_str() {
                        println!("   AI Analysis: {}", text);
                    }
                }
            }
        } else {
            println!("   Raw Response: {}", response_text);
        }
        
        println!("🎉 Claude API integration working!");
    } else {
        let error_text = response.text().await?;
        println!("❌ Claude API Error: {}", error_text);
    }
    
    Ok(())
}
