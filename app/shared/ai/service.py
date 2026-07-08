from .ai import AI


class AIService:
    def __init__(self, client: AI):
        self.client: AI = client

    async def explain_temporal_complexity(
        self, time_complexity: str, max_loop_depth: int, recursive: bool
    ) -> str:
        prompt = f"""
            You are an expert computer science educator. Analyze the following time complexity result 
            and explain it clearly to a developer.

            ## Complexity Analysis Result
            - **Time Complexity**: {time_complexity}
            - **Max Loop Depth**: {max_loop_depth}
            - **Is Recursive**: {recursive}

            ## Your Task
            Explain in 2-3 short paragraphs:
            1. What {time_complexity} means in plain terms
            2. Why the code was classified with this notation based on the analysis details above
            3. What practical impact this has on performance (e.g. how it behaves with large inputs)

            ## Rules
            - Be direct and concise, no fluff
            - Use simple analogies when helpful
            - Avoid unnecessary jargon
            - Target audience: mid-level developer
        """

        response = await self.client.create_response(
            model="llama-3.3-70b-versatile", prompt=prompt
        )

        return self.client.first_content(response)

    async def explain_spatial_complexity(
        self,
        space_complexity: str,
        total_allocations: int,
        list_allocations: int,
        dict_allocations: int,
        set_allocations: int,
        comprehensions: int,
        generator_expressions: int,
        dynamic_growth_operations: int,
        recursive_functions: int,
    ) -> str:

        prompt = f"""
            You are an expert computer science educator specializing in algorithm and memory analysis.

            ## Space Complexity Analysis Result

            - Space Complexity: {space_complexity}
            - Total Allocations: {total_allocations}
            - List Allocations: {list_allocations}
            - Dictionary Allocations: {dict_allocations}
            - Set Allocations: {set_allocations}
            - Comprehensions: {comprehensions}
            - Generator Expressions: {generator_expressions}
            - Dynamic Growth Operations: {dynamic_growth_operations}
            - Recursive Functions: {recursive_functions}

            ## Your Task

            Explain in 2–3 short paragraphs:

            1. What {space_complexity} space complexity means in practical terms
            2. Why the algorithm was classified with this complexity based on the memory-related patterns detected above
            3. What impact this has on memory consumption as the input size grows

            ## Important Analysis Rules

            - If generator expressions are used, explain that generators are memory-efficient because they evaluate lazily
            - If dynamic growth operations exist (append, dynamic insertions, etc.), explain that memory usage can grow with input size
            - If recursive functions exist, explain stack memory usage
            - If comprehensions exist, explain that they allocate additional memory structures

            ## Style Rules

            - Be concise and technically accurate
            - Avoid unnecessary jargon
            - Use clear developer-oriented explanations
            - Use analogies only when helpful
            - Do not simply repeat the raw metrics
            - Focus on what the metrics imply
            - Target audience: mid-level developer
        """

        response = await self.client.create_response(
            model="llama-3.3-70b-versatile",
            prompt=prompt,
        )

        return self.client.first_content(response)
