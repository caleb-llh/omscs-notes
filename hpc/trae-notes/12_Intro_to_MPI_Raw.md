# Intro_to_MPI Raw Transcript

## 268 - Introduction
Armed with an abstract model of a message-passing algorithm, what about a programming model that implements it so that we can write an actual program. That's the topic of this lesson. It's a particular library standard called the message passing interface, or MPI for short. Now I've picked out a couple of things for you to read so that you can get familiar with how MPI works. The main things I want you to keep an eye out for are how to do hello world in MPI. How to do asynchronous sends and receives using the routines MPI I send, I receive, wait, and wait all. How to use the built in collective operations like barriers, reductions, scatters, gathers, all to alls. And finally, what the heck is a communicator? MPI_COMM_WORLD, what is that? Now, sometime after you're done, I'm sure there will be an assignment of some sort to give you hands on experience with MPI. So pay attention!

