
# Embedding Structure
- A Lambda processes batches of HyDE Dynamo entries at a time
    - Do we even need a Lambda? Does this need to be that scalable?
    - The Lambda would make the call to the Bedrock model and pass the prompt, etc.
    - Having a Lambda making the Bedrock API call is not a terrible idea; allows for parallelism managed by the CDK and not bound by local machines
    - We'd ask some model to stitch together the information in the HyDE embeddings into some cohesive sentence, paragraph, or phrase
    - The phrase would then be embedded
    - Generic form--e.g.,
        - "The patient is taking medications X, Y, Z, has been observed to have A, B, and C, and has conditions Q, R, S"
        - We'd extract records from the text document and construct phrases like this
        - Then do simple semantic matches, providing confidences
- Make API calls from a local machine, processing Dynamo entries into documents and then embedding vectors
- Probably pass in a batch of patient records and ask to construct

- How would we do patient embeddings?
    - Simply do some semantic document matching between the patient document and the possible CSDi codes?
    - Patients with large supersets (e.g., with medications, observations, and conditions matching a large numnber of CSDi codes) might not be very semantically similar
    - Perhaps we could just focus on semantic matching of *individual* records with their likely CSDi codes?


## Embedding Patient Data
The goal is to translate sets of patient records to embedding vectors that we can use as queries

> How do we quickly match some superset of features with the subsets that, when unioned, best cover the superset?

- "Set representation" problem

- We should probably avoid embedding individual HyDE augmentations (e.g., medications)

> How did we decide which medications to augment a CSDi code with? Should we pursue more accurate medication assignemnts

Possible strategies:
- Parse medications, observations, and conditions from a patient and map them to a format common to the CSDi dataset
- Start matching records based on semantic similarity?

## Related or sub- questions
- Suppose there's some superset S. Given possibel subsets A, B, and C, how might you find which of A, B and C are completely or nearly completely represented in S using machine learning methods?
- How might we map a superset S with to a common technical vocabulary found in A, B, and C?

## Challenges of Semantic Embedding
- Documents describing hypothetical patients end up being too similar, even when using floating point representation 
- Possibly augment with a TF-IDF representation?
    - I.e. augment the embeddings that come from an attention mechanism with an embedding from pure statistical/distributional semantics
- Apply [latent semnatic analysis](https://en.wikipedia.org/wiki/Latent_semantic_analysis)?


## Importance Weighing 
- Should we do a simple importance falloff?
- How might we make importance a function of the semantic embedding?
    - We can't really do this without ground truth

