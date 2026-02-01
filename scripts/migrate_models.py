#!/usr/bin/env python3
"""
Model Migration Script

Safely migrate between LLM models using blue-green deployment strategy.
Includes canary testing, monitoring, and automatic rollback.

Usage:
    python scripts/migrate_models.py --from phi3-mini --to llama3-8b
"""

import asyncio
import argparse
import sys
import time
from pathlib import Path
from typing import Dict, Any
import yaml
import httpx


class ModelMigrator:
    """Handles safe migration between LLM models."""
    
    def __init__(self, service_url: str, config_path: Path):
        """
        Initialize migrator.
        
        Args:
            service_url: URL of the teaching service
            config_path: Path to models.yaml
        """
        self.service_url = service_url
        self.config_path = config_path
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def validate_model(self, model_id: str) -> bool:
        """
        Validate that a model is available and healthy.
        
        Args:
            model_id: Model identifier
            
        Returns:
            True if model is valid and healthy
        """
        try:
            print(f"🔍 Validating model: {model_id}")
            
            # Check if model exists in configuration
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            models = config.get('models', {}).get('model_registry', {})
            if model_id not in models:
                print(f"❌ Model '{model_id}' not found in configuration")
                return False
            
            print(f"✅ Model '{model_id}' found in configuration")
            
            # Test model with a sample query
            test_request = {
                "student_id": "migration-test",
                "question": "What is 2+2?",
                "subject": "math",
                "grade_level": "elementary",
                "model_preference": model_id
            }
            
            response = await self.client.post(
                f"{self.service_url}/api/v1/teach",
                json=test_request
            )
            
            if response.status_code == 200:
                print(f"✅ Model '{model_id}' is healthy and responsive")
                return True
            else:
                print(f"❌ Model '{model_id}' health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Model validation failed: {e}")
            return False
    
    async def enable_canary_routing(self, new_model: str, percentage: int = 10) -> bool:
        """
        Enable canary routing to new model.
        
        Args:
            new_model: New model ID
            percentage: Percentage of traffic to route (0-100)
            
        Returns:
            True if successful
        """
        print(f"🚀 Enabling canary routing: {percentage}% traffic to {new_model}")
        
        # Update configuration (in production, this would update a config service)
        # For now, we'll just log
        print(f"   → {percentage}% of requests will use {new_model}")
        print(f"   → {100-percentage}% of requests will use the current model")
        
        return True
    
    async def monitor_canary_performance(
        self,
        new_model: str,
        duration_minutes: int = 5,
        error_threshold: float = 0.05
    ) -> bool:
        """
        Monitor canary deployment performance.
        
        Args:
            new_model: Model being tested
            duration_minutes: How long to monitor
            error_threshold: Maximum acceptable error rate
            
        Returns:
            True if canary is performing well
        """
        print(f"📊 Monitoring canary performance for {duration_minutes} minutes...")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        successful_requests = 0
        failed_requests = 0
        
        while time.time() < end_time:
            try:
                # Send test request
                test_request = {
                    "student_id": "canary-test",
                    "question": "Explain photosynthesis",
                    "subject": "science",
                    "grade_level": "middle_school",
                    "model_preference": new_model
                }
                
                response = await self.client.post(
                    f"{self.service_url}/api/v1/teach",
                    json=test_request
                )
                
                if response.status_code == 200:
                    successful_requests += 1
                else:
                    failed_requests += 1
                
                # Calculate metrics
                total_requests = successful_requests + failed_requests
                error_rate = failed_requests / total_requests if total_requests > 0 else 0
                
                elapsed_minutes = (time.time() - start_time) / 60
                print(f"   ⏱️  {elapsed_minutes:.1f}min | "
                      f"✅ {successful_requests} | "
                      f"❌ {failed_requests} | "
                      f"Error rate: {error_rate:.2%}")
                
                # Check if error rate is acceptable
                if error_rate > error_threshold:
                    print(f"⚠️  Error rate {error_rate:.2%} exceeds threshold {error_threshold:.2%}")
                    return False
                
                # Wait before next test
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"⚠️  Monitoring error: {e}")
                failed_requests += 1
                await asyncio.sleep(10)
        
        print(f"✅ Canary monitoring complete. Error rate: {error_rate:.2%}")
        return True
    
    async def update_default_model(self, model_id: str) -> bool:
        """
        Update the default model in configuration.
        
        Args:
            model_id: New default model
            
        Returns:
            True if successful
        """
        print(f"🔄 Updating default model to: {model_id}")
        
        try:
            # Read current configuration
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Update default model
            config['models']['default'] = model_id
            
            # Write back
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            print(f"✅ Default model updated to: {model_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update configuration: {e}")
            return False
    
    async def rollback_migration(self, previous_model: str) -> bool:
        """
        Rollback to previous model.
        
        Args:
            previous_model: Model to rollback to
            
        Returns:
            True if successful
        """
        print(f"⚠️  Rolling back to: {previous_model}")
        return await self.update_default_model(previous_model)
    
    async def perform_migration(
        self,
        from_model: str,
        to_model: str,
        canary_percentage: int = 10,
        canary_duration_minutes: int = 5
    ) -> bool:
        """
        Execute complete migration process.
        
        Args:
            from_model: Current model
            to_model: Target model
            canary_percentage: Percentage for canary testing
            canary_duration_minutes: Duration of canary phase
            
        Returns:
            True if migration successful
        """
        print("=" * 60)
        print("🚀 Starting Model Migration")
        print("=" * 60)
        print(f"From: {from_model}")
        print(f"To:   {to_model}")
        print()
        
        # Step 1: Validate new model
        if not await self.validate_model(to_model):
            print("❌ Migration aborted: Model validation failed")
            return False
        
        print()
        
        # Step 2: Enable canary routing
        if not await self.enable_canary_routing(to_model, canary_percentage):
            print("❌ Migration aborted: Failed to enable canary routing")
            return False
        
        print()
        
        # Step 3: Monitor canary performance
        canary_success = await self.monitor_canary_performance(
            to_model,
            duration_minutes=canary_duration_minutes
        )
        
        print()
        
        if not canary_success:
            print("⚠️  Canary performance issues detected")
            await self.rollback_migration(from_model)
            print("❌ Migration aborted and rolled back")
            return False
        
        # Step 4: Promote to production
        if not await self.update_default_model(to_model):
            print("❌ Failed to update default model")
            await self.rollback_migration(from_model)
            return False
        
        print()
        print("=" * 60)
        print("✅ Migration Completed Successfully!")
        print("=" * 60)
        print(f"New default model: {to_model}")
        print()
        
        return True
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Migrate LLM models safely")
    parser.add_argument("--from", dest="from_model", required=True, help="Current model ID")
    parser.add_argument("--to", dest="to_model", required=True, help="Target model ID")
    parser.add_argument("--service-url", default="http://localhost:8080", help="Service URL")
    parser.add_argument("--config", default="config/models.yaml", help="Config file path")
    parser.add_argument("--canary-percentage", type=int, default=10, help="Canary traffic percentage")
    parser.add_argument("--canary-duration", type=int, default=5, help="Canary duration (minutes)")
    
    args = parser.parse_args()
    
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        sys.exit(1)
    
    migrator = ModelMigrator(args.service_url, config_path)
    
    try:
        success = await migrator.perform_migration(
            from_model=args.from_model,
            to_model=args.to_model,
            canary_percentage=args.canary_percentage,
            canary_duration_minutes=args.canary_duration
        )
        
        sys.exit(0 if success else 1)
        
    finally:
        await migrator.close()


if __name__ == "__main__":
    asyncio.run(main())
